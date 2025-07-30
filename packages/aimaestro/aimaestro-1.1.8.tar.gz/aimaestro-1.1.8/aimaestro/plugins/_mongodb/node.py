# -*- encoding: utf-8 -*-
from aimaestro.abcglobal.key import *
from aimaestro.plugins._mongodb.mongo_client import MongoClient

__all__ = [
    'query_node_list',
    'node_insert_one'
]


class NodeAPI(MongoClient):
    """
        DatabaseNodes class is used to manage database nodes.
    """

    _table_name = TABLE_NAME_NODES


def query_node_list(query: dict, field: dict, limit: int, skip_no: int):
    """
    Query the list of nodes from the database.
    Args:
        query (dict): The query criteria.
        field (dict): The fields to include in the result.
        limit (int): The maximum number of results to return.
        skip_no (int): The number of results to skip.
    Returns:
        list: The list of services.
    """
    _database_nodes = NodeAPI()
    return _database_nodes.query_list_sort(query=query, field=field, limit=limit, skip_no=skip_no)


def node_insert_one(query: dict, data: dict):
    """
    Insert a single document into the collection.

    Args:
        data (dict): A dictionary containing the data to insert.
        query (dict): A dictionary specifying the query criteria.
    """
    _database_nodes = NodeAPI()
    _database_nodes.update_many(query=query, update_data=data, upsert=True)
