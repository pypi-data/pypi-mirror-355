# -*- encoding: utf-8 -*-
from aimaestro.abcglobal.key import *
from aimaestro.plugins._mongodb.mongo_client import MongoClient

__all__ = [
    'query_user_list',
    'query_user_only',
    'insert_user'
]


class UserAPI(MongoClient):
    """
        DatabaseTasks class is used to manage database task - related operations.
    """
    _table_name = TABLE_NAME_USERS


def query_user_list(query: dict, field: dict, limit: int, skip_no: int):
    """
    Query the list of tasks from the database.
    Args:
        query (dict): The query criteria.
        field (dict): The fields to include in the result.
        limit (int): The maximum number of results to return.
        skip_no (int): The number of results to skip.
    Returns:
        list: The list of services.
    """
    _database_users = UserAPI()
    return _database_users.query_list_sort(query=query, field=field, limit=limit, skip_no=skip_no)


def query_user_only(query: dict, field: dict):
    _database_users = UserAPI()
    return _database_users.query_one(query=query, field=field)


def insert_user(data: dict):
    _database_users = UserAPI()
    return _database_users.insert_data(data=data)
