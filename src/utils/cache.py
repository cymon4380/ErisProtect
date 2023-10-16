import logging
from pymongo import MongoClient
from os import getenv
from config.config_loader import config_file

client = MongoClient(getenv('MONGO_AUTH_STRING'))
database = client[config_file.get('MONGO_DATABASE_NAME')]


class Collection:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.data = {}

        for document in database[self.collection_name].find():
            self.data[document['_id']] = document

        logging.info(f'Collection initialized: {collection_name}')

    def get_document(self, _id, default=None) -> dict:
        return self.data.get(_id, default)

    def get_value(self, _id, key: str, default=None):
        document = self.get_document(_id)

        if document is None:
            return default

        value = document.get(key, default)

        return value

    def set_value(self, _id, key: str, value):
        if _id not in self.data:
            self.data[_id] = {}

        self.data[_id][key] = value
        database[self.collection_name].update_one(
            {'_id': _id},
            {'$set': {key: value}},
            upsert=True
        )

    def set_values(self, _id, data: dict):
        if _id not in self.data:
            self.data[_id] = {}

        for key, value in data.items():
            self.data[_id][key] = value
        database[self.collection_name].update_one(
            {'_id': _id},
            {'$set': data},
            upsert=True
        )

    def delete_key(self, _id, key: str) -> bool:
        if _id not in self.data:
            return False
        if key not in self.data[_id]:
            return False

        del self.data[_id][key]
        database[self.collection_name].update_one(
            {'_id': _id},
            {'$unset': {key: True}},
            upsert=True
        )

        return True

    def delete_keys(self, _id, data: dict):
        if _id not in self.data:
            return

        for key in data.keys():
            if key in self.data:
                del self.data[key]
        database[self.collection_name].update_one(
            {'_id': _id},
            {'$unset': data},
            upsert=True
        )

    def delete_document(self, _id):
        if _id not in self.data:
            return
        del self.data[_id]

        database[self.collection_name].delete_one({'_id': _id})
