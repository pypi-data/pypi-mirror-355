# -*- encoding: utf-8 -*-
from aimaestro.abcglobal.key import *
from aimaestro.plugins._mongodb.mongo_client import MongoClient

__all__ = [
    'query_task_list',
    'task_insert_one',
    'query_task_status_by_task_id',
    'task_stop',
    'task_retry',
    'query_run_task'
]


class TaskAPI(MongoClient):
    """
        DatabaseTasks class is used to manage database task - related operations.
    """
    _table_name = TABLE_NAME_TASKS


def query_task_list(query: dict, field: dict, limit: int, skip_no: int):
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
    _database_tasks = TaskAPI()
    return _database_tasks.query_list_sort(query=query, field=field, limit=limit, skip_no=skip_no)


def task_insert_one(query: dict, data: dict):
    """
    Insert a single document into the collection.

    Args:
        data (dict): A dictionary containing the data to insert.
        query (dict): A dictionary specifying the query criteria.
    """
    _database_tasks = TaskAPI()
    _database_tasks.update_many(query=query, update_data=data, upsert=True)


def query_task_status_by_task_id(task_id: str):
    """
    Retrieve the task status by the given task ID.

    Args:
        task_id (str): The unique identifier of the task.

    Returns:
        dict: The first document containing the task status information.
    """
    _database_tasks = TaskAPI()
    data = _database_tasks.query_all(
        query={KEY_TASK_ID: task_id},
        field={
            '_id': 0, KEY_TASK_STATUS: 1,
            '{}.{}'.format(KEY_TASK_BODY, KEY_TASK_IS_SUB_TASK_ALL_FINISH): 1
        }
    )
    data = [i for i in data]
    return data[0]


def task_stop(task_id: str):
    """
    Stop a task by the given task ID.
    Args:
        task_id (str): The unique identifier of the task.
    Returns:
        None
    """
    _database_tasks = TaskAPI()
    _database_tasks.update_many(
        query={KEY_TASK_ID: task_id}, update_data={KEY_TASK_STATUS: KEY_TASK_STOP_STATUS})
    _database_tasks.update_many(
        query={KEY_TASK_SOURCE_ID: task_id}, update_data={KEY_TASK_STATUS: KEY_TASK_STOP_STATUS})


def task_retry(task_id: str):
    """
    Stop a task by the given task ID.
    Args:
        task_id (str): The unique identifier of the task.
    Returns:
        None
    """

    _database_tasks = TaskAPI()
    _database_tasks.update_many(
        query={KEY_TASK_ID: task_id}, update_data={KEY_TASK_STATUS: KEY_TASK_WAIT_STATUS})
    _database_tasks.update_many(
        query={KEY_TASK_SOURCE_ID: task_id}, update_data={KEY_TASK_STATUS: KEY_TASK_WAIT_STATUS})


def query_run_task(query: dict):
    """
    Retrieve a list of tasks from the collection based on the given query, sorted by task weight.

    Args:
        query (dict): A dictionary representing the query conditions for filtering the tasks.

    Returns:
        list: A list of tasks that match the specified query, sorted by task weight in descending order.
    """
    _database_tasks = TaskAPI()
    return _database_tasks.query_list_sort(
        query=query, field={'_id': 0}, limit=1000, skip_no=0, sort_field=KEY_TASK_WEIGHT)
