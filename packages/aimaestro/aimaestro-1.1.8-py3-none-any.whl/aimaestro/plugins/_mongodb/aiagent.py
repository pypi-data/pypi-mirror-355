# -*- encoding: utf-8 -*-
from aimaestro.abcglobal.key import *
from aimaestro.plugins._mongodb.mongo_client import MongoClient

__all__ = [
    'query_dialogues',
    'dialogues_insert_one',
    'query_dialogue_message',
    'dialogues_message_insert_one',
    'query_one_dialogue'
]


class Dialogues(MongoClient):
    """
        DatabaseNodes class is used to manage database dialogues.
    """

    _table_name = TABLE_NAME_DIALOGUES


class DialogueMessage(MongoClient):
    """
        DatabaseNodes class is used to manage database dialogue message.
    """
    _table_name = TABLE_NAME_DIALOGUE_MESSAGE


def query_dialogues(query: dict, field: dict, limit: int, skip_no: int):
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
    _api = Dialogues()
    return _api.query_list_sort(query=query, field=field, limit=limit, skip_no=skip_no)


def query_one_dialogue(dialogue_id: str):
    """
    Query the list of nodes from the database.
    Args:
        dialogue_id (dict): The query criteria.
    Returns:
        list: The list of services.
    """
    _api = Dialogues()
    return _api.query_one(query={'dialogue_id': dialogue_id}, field={'_id': 0})


def dialogues_insert_one(query: dict, data: dict):
    """
    Insert a single document into the collection.

    Args:
        data (dict): A dictionary containing the data to insert.
        query (dict): A dictionary specifying the query criteria.
    """
    _api = Dialogues()
    _api.update_many(query=query, update_data=data, upsert=True)


def query_dialogue_message(query: dict, field: dict, limit: int, skip_no: int,
                           sort_field: str = 'create_time', sort: int = 1):
    """
    Query the list of nodes from the database.
    Args:
        query (dict): The query criteria.
        field (dict): The fields to include in the result.
        limit (int): The maximum number of results to return.
        skip_no (int): The number of results to skip.
        sort_field (str): The field to sort by.
        sort (int): The sort order. 1 for ascending, -1 for descending.
    Returns:
        list: The list of services.
    """
    _api = DialogueMessage()
    return _api.query_list_sort(
        query=query, field=field, limit=limit, skip_no=skip_no, sort_field=sort_field, sort=sort)


def dialogues_message_insert_one(query: dict, data: dict):
    """
    Insert a single document into the collection.

    Args:
        data (dict): A dictionary containing the data to insert.
        query (dict): A dictionary specifying the query criteria.
    """
    _api = DialogueMessage()
    _api.update_many(query=query, update_data=data, upsert=True)
