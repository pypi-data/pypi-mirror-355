import os
from pymongo import MongoClient
from pymongo.collection import Collection

class MongoDBClient:
    """
    MongoDB client handler for safe usage in forking environments.
    Lazily initializes a client to avoid fork-safety warnings.
    """

    def __init__(self, user: str = 'SharedData') -> None:
        """
        Initialize MongoDB client handler.
        
        Args:
            user (str): The database user namespace. Defaults to 'SharedData'.
        """
        self._user = user
        self.mongodb_conn_str = (
            f'mongodb://{os.environ["MONGODB_USER"]}:'
            f'{os.environ["MONGODB_PWD"]}@'
            f'{os.environ["MONGODB_HOST"]}:'
            f'{os.environ["MONGODB_PORT"]}/'
        )
        self._client = None  # Client will be created on first access

    @property
    def client(self) -> MongoClient:
        """
        Lazily initialize the MongoClient for this process.
        """
        if self._client is None:
            self._client = MongoClient(self.mongodb_conn_str)
        return self._client

    @client.setter
    def client(self, value: MongoClient) -> None:
        """
        Manually set the MongoDB client.
        """
        self._client = value

    def __getitem__(self, collection_name: str) -> Collection:
        """
        Allow dictionary-like access to collections in the user's database.
        
        Args:
            collection_name (str): The name of the collection to access.
        
        Returns:
            Collection: The requested MongoDB collection.
        """
        return self.client[self._user][collection_name]