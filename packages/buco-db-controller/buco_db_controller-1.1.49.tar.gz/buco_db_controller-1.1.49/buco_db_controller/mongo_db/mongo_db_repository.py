from typing import List

from pymongo import UpdateOne
from buco_db_controller.mongo_db.mongo_db import MongoDB


class MongoDBBaseRepository(MongoDB):
    def __init__(self, db_name):
        super().__init__(db_name)

    def insert_document(self, collection_name, document):
        collection = self.db[collection_name]
        collection.insert_one(document)

    def insert_many_documents(self, collection_name, documents):
        collection = self.db[collection_name]
        collection.insert_many(documents)

    def find_document(self, collection_name, query) -> dict:
        collection = self.db[collection_name]
        return collection.find_one(query)

    def find_documents(self, collection_name: str, query: dict) -> List[dict]:
        collection = self.db[collection_name]
        return list(collection.find(query))

    def update_document(self, collection_name, query, update):
        collection = self.db[collection_name]
        collection.update_one(query, {'$set': update})

    def delete_document(self, collection_name, query):
        collection = self.db[collection_name]
        collection.delete_one(query)

    def upsert_document(self, collection_name, item):
        collection = self.db[collection_name]

        query = {'parameters': item['parameters']}
        update = {'$set': item}

        collection.update_one(query, update, upsert=True)

    def bulk_upsert_documents(self, collection_name, data):
        collection = self.db[collection_name]
        operations = []

        for item in data:
            query = {'parameters': item['parameters']}
            update = {'$set': item}
            operations.append(UpdateOne(query, update, upsert=True))

        if operations:
            collection.bulk_write(operations)
