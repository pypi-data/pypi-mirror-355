import os
from pymongo import MongoClient

# Load environment variables or set defaults
# MONGO_URI = os.getenv('MONGO_URI', 'mongodb://192.168.0.250:27017/')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
_mongo_client = None


def get_mongo_client():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URI, maxPoolSize=300)
    return _mongo_client


class MongoDB:
    def __init__(self, db_name):
        self.client = get_mongo_client()
        self.db = self.client[db_name]

    def get_db(self):
        """
        Return MongoDB instance
        """
        return self.db

    def close(self):
        self.client.close()
