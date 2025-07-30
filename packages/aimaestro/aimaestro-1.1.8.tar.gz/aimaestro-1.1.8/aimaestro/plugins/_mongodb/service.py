# -*- encoding: utf-8 -*-
from aimaestro.abcglobal.key import *
from aimaestro.plugins._mongodb.mongo_client import MongoClient

__all__ = [
    'query_service_list',
    'service_insert_one',
    'update_work_max_process',
    'query_worker_running_number',
    'worker_push_process',
    'worker_pull_process'
]


class ServiceAPI(MongoClient):
    """
        DatabaseServices class is used to manage database services - related operations.
    """
    _table_name = TABLE_NAME_SERVICES


def query_service_list(query: dict, field: dict, limit: int, skip_no: int):
    """
    Query the list of services from the database.
    Args:
        query (dict): The query criteria.
        field (dict): The fields to include in the result.
        limit (int): The maximum number of results to return.
        skip_no (int): The number of results to skip.
    Returns:
        list: The list of services.
    """
    _database_services = ServiceAPI()

    return _database_services.query_list_sort(query=query, field=field, limit=limit, skip_no=skip_no)


def service_insert_one(query: dict, data: dict):
    """
    Insert a single document into the collection.

    Args:
        data (dict): A dictionary containing the data to insert.
        query (dict): A dictionary specifying the query criteria.
    """
    _database_services = ServiceAPI()
    _database_services.update_many(query=query, update_data=data, upsert=True)


def query_worker_running_number(query: dict):
    """
    Query the number of running workers based on the given query.
    Args:
        query (dict): A dictionary containing the query criteria.
    Returns:
        tuple: A tuple containing the number of running workers and the maximum number of workers.
    """
    _database_services = ServiceAPI()
    data = _database_services.query_all(
        query=query,
        field={'_id': 0, KEY_WORKER_RUN_PROCESS: 1, KEY_WORKER_MAX_PROCESS: 1}
    )
    return len(data[0].get(KEY_WORKER_RUN_PROCESS)), data[0].get(KEY_WORKER_MAX_PROCESS)


def update_work_max_process(worker_name: str, worker_ipaddr: str, worker_max_process: int):
    """
    Update the maximum number of processes for a worker identified by its name and IP address.

    Args:
        worker_name (str): The name of the worker.
        worker_ipaddr (str): The IP address of the worker.
        worker_max_process (int): The new maximum number of processes for the worker.

    Returns:
        None
    """
    _database_services = ServiceAPI()
    _database_services.update_many(
        query={
            KEY_WORKER_NAME: worker_name,
            KEY_WORKER_IPADDR: worker_ipaddr
        },
        update_data={
            KEY_WORKER_MAX_PROCESS: worker_max_process
        }
    )


def worker_push_process(worker_name: str, worker_ipaddr: str, worker_pid: int):
    """
    Update the maximum number of processes for a worker identified by its name and IP address.
    Args:
        worker_name (str): The name of the worker.
        worker_ipaddr (str): The IP address of the worker.
        worker_pid (int): The new maximum number of processes for the worker.
    Returns:
        None
    """
    _database_services = ServiceAPI()
    _database_services.push_one(
        query={
            KEY_WORKER_NAME: worker_name,
            KEY_WORKER_IPADDR: worker_ipaddr
        },
        update_data={
            KEY_WORKER_RUN_PROCESS: worker_pid
        }
    )


def worker_pull_process(worker_name: str, worker_ipaddr: str, worker_pid: int):
    """
    Update the maximum number of processes for a worker identified by its name and IP address.
    Args:
        worker_name (str): The name of the worker.
        worker_ipaddr (str): The IP address of the worker.
        worker_pid (int): The new maximum number of processes for the worker.
    Returns:
        None
    """

    _database_services = ServiceAPI()
    _database_services.pull_one(
        query={
            KEY_WORKER_NAME: worker_name,
            KEY_WORKER_IPADDR: worker_ipaddr
        },
        update_data={
            KEY_WORKER_RUN_PROCESS: worker_pid
        }
    )
