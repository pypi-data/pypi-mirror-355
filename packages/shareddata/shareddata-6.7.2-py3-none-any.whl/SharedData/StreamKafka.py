import os
import time
import uuid
import threading
import bson
import lz4.frame
import asyncio
import queue

from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import Consumer, KafkaError        

from SharedData.Database import DATABASE_PKEYS
from SharedData.Logger import Logger

class StreamKafka:

    def __init__(
        self,
        database, period, source, tablename,
        user='master',
        bootstrap_servers=None,
        replication=None,
        partitions=None,
        retention=259200000,
        use_aiokafka=False
    ):
        self.user = user
        self.database = database
        self.period = period
        self.source = source
        self.tablename = tablename
        self.use_aiokafka = use_aiokafka
        self.topic = f'{user}/{database}/{period}/{source}/stream/{tablename}'.replace('/','-')

        if bootstrap_servers is None:
            bootstrap_servers = os.environ['KAFKA_BOOTSTRAP_SERVERS']
        self.bootstrap_servers = bootstrap_servers
        
        if replication is None:
            self.replication = int(os.environ['KAFKA_REPLICATION'])
        else:
            self.replication = replication
        
        if partitions is None:
            self.partitions = int(os.environ['KAFKA_PARTITIONS'])
        else:
            self.partitions = partitions

        if retention is None:
            self.retention = int(os.environ['KAFKA_RETENTION'])
        else:
            self.retention = retention

        self.lock = threading.Lock()
        self.pkeys = DATABASE_PKEYS[database]

        self._producer = None
        self._producer_thread = None

        self._consumers = []
        self._consumer_threads = []
        if use_aiokafka:
            self.consumer_queue = asyncio.Queue()
            self.producer_queue = asyncio.Queue()
        else:
            self.consumer_queue = queue.Queue()
            self.producer_queue = queue.Queue()
                
        admin = AdminClient({'bootstrap.servers': self.bootstrap_servers})
        # create topic if not exists
        if not self.topic in admin.list_topics().topics:
            new_topic = NewTopic(
                self.topic, 
                num_partitions=self.partitions, 
                replication_factor=self.replication,
                config={"retention.ms": str(self.retention)} 
            )
            fs = admin.create_topics([new_topic])
            for topic, f in fs.items():
                try:
                    f.result()
                    time.sleep(2)
                    Logger.log.debug(f"Topic {topic} created.")
                except Exception as e:
                    print(f"(May be already created!) {e}")
        else:
            #get number of partitions
            self.partitions = len(admin.list_topics(topic=self.topic).topics[self.topic].partitions)

    #
    # Producer sync (confluent) and async (aiokafka)
    #
    @property
    def producer(self):
        if self.use_aiokafka:
            raise RuntimeError("Use 'await get_async_producer()' in aiokafka mode.")
        with self.lock:
            if self._producer is None:
                from confluent_kafka import Producer
                self.bootstrap_servers = os.getenv('KAFKA_BOOSTRAP_SERVERS')
                if self.bootstrap_servers is None:
                    raise Exception('Kafka self.bootstrap_servers not set')            
                self._producer = Producer({'bootstrap.servers': self.bootstrap_servers})
            return self._producer

    async def get_async_producer(self):
        if not self.use_aiokafka:
            raise RuntimeError("This method is only available in aiokafka mode.")
        if self._producer is None:
            from aiokafka import AIOKafkaProducer            
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,                
            )
            
            await self._producer.start()
        return self._producer

    #
    # Extend (produce) sync/async
    #
    def extend(self, data):
        if self.use_aiokafka:
            raise RuntimeError("Use 'await async_extend(...)' in aiokafka mode.")
        if self._producer_thread is None:
            self._producer_thread = threading.Thread(self.producer_loop_thread)
            self._producer_thread.start()

        if isinstance(data, list):
            for msg in data:
                for pkey in self.pkeys:
                    if not pkey in msg:
                        raise Exception(f'extend(): Missing pkey {pkey} in {msg}')
                if not 'mtime' in msg:
                    msg['mtime'] = time.time_ns()
                message = lz4.frame.compress(bson.BSON.encode(msg))
                self.producer_queue.put(message)
                # self.producer.produce(self.topic, value=message)
        elif isinstance(data, dict):
            for pkey in self.pkeys:
                if not pkey in data:
                    raise Exception(f'extend(): Missing pkey {pkey} in {data}')
            if not 'mtime' in data:
                data['mtime'] = time.time_ns()            
            message = lz4.frame.compress(bson.BSON.encode(data))
            self.producer_queue.put(message)
            # self.producer.produce(self.topic, value=message)
        else:
            raise Exception('extend(): Invalid data type')                
      
        # Wait up to 5 seconds
        result = self.producer.flush(timeout=5.0)
        if result > 0:
            raise Exception(f"Failed to flush {result} messages")
        
    def producer_loop_thread(self):
        BATCH_SIZE = 10000
        while True:            
            msg = self.producer_queue.get()
            self.producer.produce(self.topic, value=msg)
            msgcount = 1
            while msgcount < BATCH_SIZE and not self.producer_queue.empty():
                self.producer.produce(self.topic, value=msg)
                msgcount+=1            
            
            trials = 3
            while trials > 0:
                result = self.producer.flush(timeout=30.0)
                if result > 0:
                    trials-=1
                else:
                    break            
            if trials <= 0:
                raise Exception(f"Failed to flush {result} messages")        

    async def async_extend(self, data):
        if not self.use_aiokafka:
            raise RuntimeError("Use 'extend()' in confluent_kafka mode.")
        
        producer = await self.get_async_producer()                            
        if isinstance(data, list):
            for msg in data:
                for pkey in self.pkeys:
                    if not pkey in msg:
                        raise Exception(f'extend(): Missing pkey {pkey} in {msg}')
                if not 'mtime' in msg:
                    msg['mtime'] = time.time_ns()
                message = lz4.frame.compress(bson.BSON.encode(msg))                
                await producer.send(self.topic, value=message)
            # await producer.flush()
        elif isinstance(data, dict):
            for pkey in self.pkeys:
                if not pkey in data:
                    raise Exception(f'extend(): Missing pkey {pkey} in {data}')
            if not 'mtime' in data:
                data['mtime'] = time.time_ns()
            message = lz4.frame.compress(bson.BSON.encode(data))            
            await producer.send(self.topic, value=message)
        else:
            raise Exception('extend(): Invalid data type')
                
    
    #
    # Flush/close producer
    #
    def flush(self, timeout=5.0):
        if self.use_aiokafka:
            raise RuntimeError("Use 'await async_flush()' in aiokafka mode.")
        if self._producer is not None:
            result = self._producer.flush(timeout=timeout)
            if result > 0:
                raise Exception(f"Failed to flush {result} messages")

    async def async_flush(self):
        if not self.use_aiokafka:
            raise RuntimeError("Use 'flush()' in confluent_kafka mode.")
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None

    #
    # Consumer sync/async
    #
    def subscribe(self, groupid=None, offset = 'latest', autocommit=True, timeout=None):
        if self.use_aiokafka:
            raise RuntimeError("Use 'await async_subscribe()' in aiokafka mode.")
        
        if groupid is None:
            groupid = str(uuid.uuid4())

        self._consumers = []
        for p in range(self.partitions):
            self._consumers.append(
                Consumer({
                    'bootstrap.servers': self.bootstrap_servers,
                    'group.id': groupid,
                    'auto.offset.reset': offset,
                    'enable.auto.commit': autocommit
                })
            )
            self._consumers[p].subscribe([self.topic])
            # Wait for partition assignment
            if timeout is not None:
                start = time.time()
                while not self._consumers[p].assignment():
                    if time.time() - start > timeout:
                        raise TimeoutError("Timed out waiting for partition assignment.")
                    self._consumers[p].poll(0.1)
                    time.sleep(0.1)
        
        self.consumer_threads = []
        for p in range(self.partitions):
            self.consumer_threads.append(
                threading.Thread(target=self.consumer_thread, args=(p,))
            )
            self.consumer_threads[p].start()
        
    async def async_subscribe(self, groupid=None, offset='latest'):
        if not self.use_aiokafka:
            raise RuntimeError("Use 'subscribe()' in confluent_kafka mode.")
        from aiokafka import AIOKafkaConsumer

        if groupid is None:
            groupid = str(uuid.uuid4())

        consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=groupid,
            auto_offset_reset=offset
        )
        await consumer.start()
        self._consumers = [consumer]

        # Start just ONE consumer task for this group/topic!
        self.consumer_threads = [
            asyncio.create_task(self.async_consumer_task(0))
        ]
            

    #
    # Poll (consume one message) sync/async
    #
    def poll(self, timeout=None, consumerid=0):
        if self.use_aiokafka:
            raise RuntimeError("Use 'async_poll()' in aiokafka mode.")
        if timeout is None:
            msg = self._consumers[consumerid].poll()
        else:
            msg = self._consumers[consumerid].poll(timeout)
            
        if msg is None:
            return None
        if msg.error():
            from confluent_kafka import KafkaError
            if msg.error().code() != KafkaError._PARTITION_EOF:
                raise Exception(f"Error: {msg.error()}")
        msgdict = bson.BSON.decode(lz4.frame.decompress(msg.value()))
        return msgdict

    def consumer_thread(self, consumerid):
        while True:
            msg = self.poll(consumerid)
            if msg is not None:
                self.consumer_queue.put(msg)

    
    async def async_poll(self, consumerid=0):
        if not self.use_aiokafka:
            raise RuntimeError("Use 'poll()' in confluent_kafka mode.")
        if self._consumers[consumerid] is None:
            raise RuntimeError("You must call 'await async_subscribe()' first.")
        async for msg in self._consumers[consumerid]:
            if msg.value is not None:
                msgdict = bson.BSON.decode(lz4.frame.decompress(msg.value))
                yield msgdict
    
    async def async_consumer_task(self, consumerid):
        async for msg in self.async_poll(consumerid):
            await self.consumer_queue.put(msg)

    #
    # Retention update (sync mode only)
    #
    def set_retention(self, retention_ms):
        if self.use_aiokafka:
            raise RuntimeError("Set retention only supported in sync mode (confluent_kafka).")
        from confluent_kafka.admin import AdminClient, ConfigResource
        admin = AdminClient({'bootstrap.servers': self.bootstrap_servers})
        config_resource = ConfigResource('topic', self.topic)
        new_config = {'retention.ms': str(retention_ms)}
        fs = admin.alter_configs([config_resource], new_configs=new_config)
        for resource, f in fs.items():
            try:
                f.result()
                Logger.log.debug(f"Retention period for topic {resource.name()} updated to {retention_ms} ms.")
                return True
            except Exception as e:
                Logger.log.error(f"Failed to update retention period: {e}")
                return False

    #
    # Sync/async close for consumer (optional)
    #
    def close(self):
        for consumerid in self._consumers:
            if self._consumers[consumerid] is not None:
                self._consumers[consumerid].close()
                self._consumers[consumerid] = None

    async def async_close(self):
        for consumerid in self._consumers:
            if self._consumers[consumerid] is not None:
                await self._consumers[consumerid].stop()
                self._consumers[consumerid] = None

    def delete(self) -> bool:
        """
        Deletes the specified Kafka topic.
        Returns True if deleted, False if topic did not exist or an error occurred.
        """
        
        admin = AdminClient({'bootstrap.servers': self.bootstrap_servers})
        if self.topic not in admin.list_topics(timeout=10).topics:
            Logger.log.warning(f"Topic {self.topic} does not exist.")
            return False
        fs = admin.delete_topics([self.topic])
        for topic, f in fs.items():
            try:
                f.result()  # Wait for operation to finish
                Logger.log.debug(f"Topic {topic} deleted.")
                return True
            except Exception as e:
                Logger.log.error(f"Failed to delete topic {topic}: {e}")
                return False
        return False

        
# ========== USAGE PATTERNS ==========

# --- Synchronous / confluent_kafka ---
"""
stream = StreamKafka(
    database="mydb", period="1m", source="agg", tablename="prices",
    self.bootstrap_servers="localhost:9092",
    KAFKA_PARTITIONS=1,
    use_aiokafka=False
)
stream.extend({'price': 100, 'ts': time.time()})
stream.subscribe()
msg = stream.poll(timeout=1.0)
print(msg)
stream.close()
"""

# --- Asynchronous / aiokafka ---
"""
import asyncio

async def main():
    stream = StreamKafka(
        database="mydb", period="1m", source="agg", tablename="prices",
        self.bootstrap_servers="localhost:9092",
        KAFKA_PARTITIONS=1,
        use_aiokafka=True
    )
    await stream.async_extend({'price': 200, 'ts': time.time()})
    await stream.async_subscribe()
    async for msg in stream.async_poll():
        print(msg)
        break
    await stream.async_flush()
    await stream.async_close()

asyncio.run(main())
"""