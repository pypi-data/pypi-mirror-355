# -*- encoding: utf-8 -*-
import pymongo

from aimaestro.abcglobal.key import *

__all__ = ['initialization_mongo', 'MongoClient']

_MONGODB_CONFIG = DEFAULT_VALUE_MONGODB_URI


def initialization_mongo(config: dict):
    """
    Initialize the logger with the given configuration.
    Args:
        config (dict): A dictionary containing the configuration.
    """
    global _MONGODB_CONFIG
    _MONGODB_CONFIG = config.get(KEY_MONGO_CONFIG, DEFAULT_VALUE_MONGODB_URI)


class MongoClient:
    """
    This class is used to interact with a MongoDB database,
    providing a series of methods to operate on database collections.
    """
    _instance = None
    _table_name = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MongoClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self._client = pymongo.MongoClient(_MONGODB_CONFIG, connect=False)

    def get_collection(self):
        """
        Get the MongoDB collection object for the specified table name.

        Returns:
            pymongo.collection.Collection: A MongoDB collection object.
        """
        return self._client[KEY_PROJECT_NAME][self._table_name]

    def update_many(self, query: dict, update_data: dict, upsert=False):
        """
        Update multiple documents in the collection that match the query.

        Args:
            query (dict): A dictionary specifying the query criteria.
            update_data (dict): A dictionary containing the data to update.
            upsert (bool, optional): If True, insert a new document if no documents match the query. Defaults to False.

        Returns:
            None
        """
        collection = self.get_collection()
        collection.update_many(query, {"$set": update_data}, upsert=upsert)
        return None

    def push_many(self, query: dict, update_data: dict, upsert=False):
        """
        Push data to an array field in multiple documents that match the query.

        Args:
            query (dict): A dictionary specifying the query criteria.
            update_data (dict): A dictionary containing the data to push.
            upsert (bool, optional): If True, insert a new document if no documents match the query. Defaults to False.

        Returns:
            None
        """
        collection = self.get_collection()
        collection.update_many(query, {"$push": update_data}, upsert=upsert)
        return None

    def push_one(self, query: dict, update_data: dict, upsert=False):
        """
        Push data to an array field in the first document that matches the query.

        Args:
            query (dict): A dictionary specifying the query criteria.
            update_data (dict): A dictionary containing the data to push.
            upsert (bool, optional): If True, insert a new document if no documents match the query. Defaults to False.

        Returns:
            None
        """
        collection = self.get_collection()
        collection.find_one_and_update(query, {"$push": update_data}, upsert=upsert)
        return None

    def pull_one(self, query: dict, update_data: dict):
        """
        Pull data from an array field in the first document that matches the query.

        Args:
            query (dict): A dictionary specifying the query criteria.
            update_data (dict): A dictionary containing the data to pull.

        Returns:
            None
        """
        collection = self.get_collection()
        collection.find_one_and_update(query, {"$pull": update_data})
        return None

    def insert_data(self, data: dict):
        """
        Insert a single document into the collection.

        Args:
            data (dict): A dictionary containing the data to insert.

        Returns:
            None
        """
        collection = self.get_collection()
        collection.insert_one(data)
        return None

    def delete_data(self, query: dict):
        """
        Delete multiple documents from the collection that match the query.

        Args:
            query (dict): A dictionary specifying the query criteria.

        Returns:
            None
        """
        collection = self.get_collection()
        collection.delete_many(query)
        return None

    def query_all(self, query: dict, field: dict):
        """
        Retrieve all documents from the collection that match the query.

        Args:
            query (dict): A dictionary specifying the query criteria.
            field (dict): A dictionary specifying the fields to include or exclude in the result.

        Returns:
            list: A list of documents that match the query.
        """
        collection = self.get_collection()
        data = collection.find(query, field)
        data = [i for i in data]
        return data

    def query_count(self, query):
        """
        Get the count of documents in the collection that match the query.

        Args:
            query (dict): A dictionary specifying the query criteria.

        Returns:
            int: The count of documents that match the query.
        """
        collection = self.get_collection()
        return collection.count_documents(filter=query)

    def query_list_sort(self, query: dict, field: dict, limit: int, skip_no: int,
                        sort_field: str = 'create_time', sort: int = -1):
        """
        Retrieve a list of documents from the collection based on the given query,
        field projection, limit, skip, and sorting criteria.

        Args:
            query (dict): A dictionary specifying the query criteria.
            field (dict): A dictionary specifying the fields to include or exclude in the result.
            limit (int): The maximum number of documents to return.
            skip_no (int): The number of documents to skip before starting to return results.
            sort_field (str, optional): The field to sort the results by. Defaults to 'update_time'.
            sort (int, optional): The sorting order. -1 for descending, 1 for ascending. Defaults to -1.

        Returns:
            pymongo.cursor.Cursor: A cursor object that can be iterated over to access the documents.
        """
        collection = self.get_collection()
        data = collection.find(query, field).sort(sort_field, sort).limit(limit).skip(skip_no)
        data = [i for i in data]
        count = collection.count_documents(query)
        return count, data

    def query_one(self, query: dict, field: dict):
        """
        Retrieve a list of documents from the collection based on the given query,
        field projection, limit, skip, and sorting criteria.

        Args:
            query (dict): A dictionary specifying the query criteria.
            field (dict): A dictionary specifying the fields to include or exclude in the result.

        Returns:
            pymongo.cursor.Cursor: A cursor object that can be iterated over to access the documents.
        """
        collection = self.get_collection()
        data = collection.find_one(query, field)
        return data
