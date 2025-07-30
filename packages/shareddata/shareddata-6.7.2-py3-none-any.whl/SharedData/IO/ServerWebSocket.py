import bson
import lz4.frame
import time
import sys
import asyncio
from aiohttp import web
import json
import os
from cryptography.fernet import Fernet
import threading

from SharedData.IO.SyncTable import SyncTable
from SharedData.SharedData import SharedData

class ServerWebSocket():
    BUFF_SIZE = int(128*1024)
    clients = {}
    lock = asyncio.Lock()
    shdata = None  # needs to be initialized


    # Lock for updating users data
    users_lock = threading.Lock()
    users = {}

    @staticmethod
    def check_permissions(reqpath: list[str], permissions: dict, method: str) -> bool:
        """
        Iteratively check if given path and method are permitted.
        Faster than a classical recursive approach for deep trees.
        """    
        node = permissions
        for segment in reqpath:
            if segment in node:
                node = node[segment]
            elif '*' in node:
                node = node['*']
            else:
                return False
            # If leaf is not dict (wildcard or method list)
            if not isinstance(node, dict):
                if '*' in node or (isinstance(node, list) and method in node):
                    return True
                return False
        # At the end, check at current node
        if '*' in node:
            return True
        if method in node:
            return True
        return False
    
    @staticmethod
    async def runserver(shdata, host, port):
        ServerWebSocket.shdata = shdata
        app = web.Application()
        app.router.add_get('/', ServerWebSocket.handle_client_thread)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        Logger.log.info(f'Listening on {host}:{port}')
        await site.start()
        while True:
            await asyncio.sleep(3600)  # Keep running    

    @staticmethod
    async def handle_client_thread(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        addr = request.remote
        Logger.log.info(f"New client connected: {addr}")
        async with ServerWebSocket.lock:
            ServerWebSocket.clients[ws] = {
                'watchdog': time.time_ns(),
                'transfer_rate': 0.0,
            }
        client = ServerWebSocket.clients[ws]
        client['conn'] = ws
        client['addr'] = addr

        try:
            await ServerWebSocket.handle_client_websocket(client)
        except Exception as e:
            Logger.log.error(f"Client {addr} disconnected with error: {e}")
        finally:
            if 'stream' in client:
                await client['stream'].async_close()
            async with ServerWebSocket.lock:
                ServerWebSocket.clients.pop(ws, None)
            Logger.log.info(f"Client {addr} disconnected.")
            await ws.close()
        return ws

    @staticmethod
    async def handle_client_websocket(client):
        ws = client['conn']
        client['authenticated'] = False

        # --- LOGIN & AUTH ---
        login_msg = await ws.receive_json()        
        client['watchdog'] = time.time_ns()                    
        # authenticate                        
        token = login_msg['token']
        if not token in ServerWebSocket.users:
            time.sleep(3)
            errmsg = 'Unknown token %s authentication failed!' % (client['addr'])
            Logger.log.error(errmsg)
            await ws.send_json({'message': errmsg})
            raise Exception(errmsg)
        userdata = ServerWebSocket.users[token]
        
        client.update(login_msg)
        client['userdata'] = userdata
        
        reqpath = f"{login_msg['user']}/{login_msg['database']}/{login_msg['period']}/{client['source']}/{client['container']}/{login_msg['tablename']}"
        reqpath = reqpath.split('/')

        method = ''
        if client['action'] == 'publish':
            method = 'POST'
        elif client['action'] == 'subscribe':
            method = 'GET'
        else:
            msg = 'Unknown action: %s' % client['action']
            raise Exception(msg)

        if not ServerWebSocket.check_permissions(reqpath, userdata['permissions'], method):
            time.sleep(3)
            errmsg = 'Client %s permission denied!' % (client['addr'])
            Logger.log.error(errmsg)
            await ws.send_json({'message': errmsg})
            raise Exception(errmsg)
        
        await ws.send_json({'message': 'login success!'})
                    
        if client['action'] == 'subscribe':

            if client['container'] == 'table':
                client = SyncTable.init_client(client)
                await SyncTable.websocket_publish_loop(client)

            elif client['container'] == 'stream':
                await ServerWebSocket.stream_subscribe_loop(client)

        elif client['action'] == 'publish':

            if client['container'] == 'table':
                client = SyncTable.init_client(client)
                responsemsg = {
                    'mtime': float(client['records'].mtime),
                    'count': int(client['records'].count),
                }
                await ws.send_str(json.dumps(responsemsg))
                await SyncTable.websocket_subscription_loop(client)

            elif client['container'] == 'stream':                    
                await ServerWebSocket.stream_publish_loop(client)                

    @staticmethod
    async def stream_subscribe_loop(client: dict) -> None:
        """
        Handle a client subscribing to a streaming source over websocket.
        Batches messages for improved throughput.
        """
        conn = client['conn']
        addr = client['addr']
        client['upload'] = 0
        client['download'] = 0
        groupid = client.get('groupid', f"ws-{addr}")
        offset = client.get('offset', 'latest')
        BATCH_SIZE = 10000
        BATCH_TIMEOUT = 0.02  # seconds

        try:
            shdata = ServerWebSocket.shdata
            stream = shdata.stream(
                client['database'], client['period'], client['source'], client['tablename'],
                user=client.get('user', 'master'), use_aiokafka=True
            )
            client['stream'] = stream
            await stream.async_subscribe(groupid=groupid, offset=offset)
            while True:
                batch = []
                # Wait for first message with no timeout
                msg = await anext(stream.async_poll())
                batch.append(msg)
                # Try to fill up to BATCH_SIZE or until timeout
                for _ in range(BATCH_SIZE - 1):
                    try:
                        msg = await asyncio.wait_for(anext(stream.async_poll()), timeout=BATCH_TIMEOUT)
                        batch.append(msg)
                    except asyncio.TimeoutError:
                        break  # No more messages soon
                try:
                    _msg = lz4.frame.compress(bson.BSON.encode({'data': batch}))
                    client['upload'] += len(_msg)
                    await conn.send_bytes(_msg)
                except Exception as e:
                    Logger.log.error(f"Error sending stream batch to {addr}: {e}")
                    break
        except asyncio.CancelledError:
            Logger.log.info(f"Websocket stream with {addr} cancelled.")
        finally:
            await conn.close()
            Logger.log.info(f"Stream client {addr} connection closed.")

    @staticmethod
    async def stream_publish_loop(client: dict) -> None:
        """
        Receive BSON lz4-compressed messages from a websocket client and publish to shdata.stream.
        """
        conn = client['conn']
        addr = client['addr']
        client['upload'] = 0
        client['download'] = 0        
        try:
            shdata = ServerWebSocket.shdata
            stream = shdata.stream(
                client['database'], client['period'], client['source'], client['tablename'],
                user=client.get('user', 'master'), use_aiokafka=True
            )
            client['stream'] = stream
            while True:
                try:
                    msg_bytes = await conn.receive_bytes()
                    if not msg_bytes:
                        break
                    # Decompress and decode BSON
                    client['download'] += len(msg_bytes)
                    msg = bson.BSON.decode(lz4.frame.decompress(msg_bytes))
                    await stream.async_extend(msg['data'])
                    
                except Exception as e:
                    Logger.log.error(f"Error receiving/publishing stream message from {addr}: {e}")
                    break
        except asyncio.CancelledError:
            Logger.log.info(f"Websocket publish stream with {addr} cancelled.")
        finally:
            await conn.close()
            Logger.log.info(f"Publish stream client {addr} connection closed.")

async def send_heartbeat(host, port):
    lasttotalupload = 0
    lasttotaldownload = 0
    lasttime = time.time()
    while True:
        client_keys = list(ServerWebSocket.clients.keys())
        nclients = 0
        totalupload = 0
        totaldownload = 0
        for client_key in client_keys:
            nclients += 1
            c = ServerWebSocket.clients.get(client_key)
            if c is not None:
                totalupload += c.get('upload', 0)
                totaldownload += c.get('download', 0)
        te = time.time() - lasttime
        lasttime = time.time()
        upload = max(0, (totalupload - lasttotalupload) / te)
        download = max(0, (totaldownload - lasttotaldownload) / te)
        lasttotaldownload = totaldownload
        lasttotalupload = totalupload

        Logger.log.debug('#heartbeat#host:%s,port:%i,clients:%i,download:%.3fMB/s,upload:%.3fMB/s' \
                         % (host, port, nclients, download/1024/1024, upload/1024/1024))
        await asyncio.sleep(15)

async def main():
    await asyncio.gather(
        ServerWebSocket.runserver(shdata, host, port),
        send_heartbeat(host, port)
    )

if __name__ == '__main__':
    from SharedData.Logger import Logger
    from SharedData.SharedData import SharedData
    import argparse

    shdata = SharedData('SharedData.IO.ServerWebSocket', user='master')
    SyncTable.shdata = shdata

    # User dictionary to store user data by token
    with ServerWebSocket.users_lock:
        if ServerWebSocket.users == {}:
            user_collection = shdata.collection('Symbols', 'D1', 'AUTH', 'USERS', user='SharedData')
            _users = list(user_collection.find({}))  # Ensure we can iterate multiple times
            new_tokens = {user['token'] for user in _users}
            # Add or update users
            for user in _users:
                if user['token'] not in ServerWebSocket.users:
                    ServerWebSocket.users[user['token']] = user
                else:
                    ServerWebSocket.users[user['token']].update(user)
            # Remove users not present in the new list
            tokens_to_delete = [token for token in ServerWebSocket.users if token not in new_tokens]
            for token in tokens_to_delete:
                del ServerWebSocket.users[token]        

    parser = argparse.ArgumentParser(description='Start the ServerWebSocket.')
    parser.add_argument('--host', default='0.0.0.0', help='Host IP to bind (default: 0.0.0.0)')
    parser.add_argument('--port', default=8001, type=int, help='Port to bind (default: 8001)')
    args = parser.parse_args()

    host = args.host
    port = args.port
    Logger.log.info('ROUTINE STARTED!')
    asyncio.run(main())