import os
from pymongo import MongoClient

# Load environment variables or set defaults
# MONGO_URI = os.getenv('MONGO_URI', 'mongodb://192.168.0.250:27017/')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')


class MongoDB:
    def __init__(self, db_name, uri=MONGO_URI):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def get_db(self):
        """
        Return MongoDB instance
        """
        return self.db

    def close(self):
        self.client.close()
