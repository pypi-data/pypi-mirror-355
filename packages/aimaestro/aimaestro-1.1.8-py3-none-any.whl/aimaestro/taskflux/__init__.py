# -*- encoding: utf-8 -*-

import json
import logging

from aimaestro.plugins import *
from aimaestro.abcglobal.key import *

from aimaestro.taskflux.ameta import *
from aimaestro.taskflux.main.main import *
from aimaestro.taskflux.cipher.rsa import *
from aimaestro.taskflux.utils.parser import *
from aimaestro.taskflux.logger.logger import *
from aimaestro.taskflux.utils.network import *
from aimaestro.taskflux.queue.rabbitmq import *
from aimaestro.taskflux.utils.timeformat import *
from aimaestro.taskflux.rpc_proxy.rpc_proxy import *
from aimaestro.taskflux.rpc_proxy.decorator import *
from aimaestro.taskflux.interface.interface import *
from aimaestro.taskflux.generateId.snowflake import *
from aimaestro.taskflux.scheduler.scheduler import *

__all__ = [
    'services_registry',
    'services_start',
    'generate_keys',
    'decrypt',
    'encrypt',
    'load_config',
    'task_required_field_check',
    'logger',
    'get_ipaddr',
    'is_port_open',
    'send_message',
    'receive_message',
    "get_date_time_obj",
    "format_converted_time",
    "get_converted_time",
    "get_yes_today",
    "get_yesterday_date",
    "convert_timestamp_to_timezone",
    "get_converted_timestamp",
    "get_date_list",
    "get_week_num",
    "get_current_week",
    "is_timestamp_within_days",
    "convert_timestamp_to_timezone_obj",
    "convert_timestamp_to_timezone_str",
    'get_converted_time_float',
    'remote_call',
    'generate_unique',
    'proxy_call',
    'rpc',
    'service_running',
    'databases_send_message',
    'databases_submit_task',
    'databases_create_subtask',
    'query_node_list',
    'node_insert_one',
    'query_service_list',
    'service_insert_one',
    'update_work_max_process',
    'query_task_list',
    'task_insert_one',
    'query_task_status_by_task_id',
    'task_stop',
    'task_retry',
    'query_run_task',
    'query_worker_running_number',
    'worker_push_process',
    'worker_pull_process',
    'snowflake_id',
    'scheduler_add_job',
    'scheduler_remove_job',
    'scheduler_start',
    'scheduler_stop',
    'ServiceConstructor',
    'WorkerConstructor',
    'initialization_taskflux',
    'loguru'
]


def initialization_taskflux(config: dict, is_cipher: bool = False):
    """
        TaskFlux is a singleton class designed to manage and schedule RPC services.
        It initializes various components such as logging, message queues, RPC proxies,
        and databases based on the provided configuration.

        Example usage:
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))

            config = {
                'MONGODB_CONFIG': 'mongodb://scheduleAdmin:scheduleAdminPasswrd@127.0.0.1:27017',
                'RABBITMQ_CONFIG': 'amqp://scheduleAdmin:scheduleAdminPasswrd@127.0.0.1:5672',
                'ROOT_PATH': current_dir
            }

            initialization_taskflux(config=config)
    """
    if KEY_ROOT_PATH not in config:
        raise Exception('Error ROOT_PATH not in config')

    if is_cipher:
        cipher_config = encrypt(plaintext=config[KEY_CIPHER_CIPHERTEXT], public_key=config[KEY_CIPHER_PUBLIC_KEY])
        config_dict = json.loads(cipher_config)
        config_dict[KEY_ROOT_PATH] = config[KEY_ROOT_PATH]
    else:
        config_dict = config

    initialization_global_attr(config_dict)


def loguru(filename: str = None, task_id: str = None) -> logging.Logger:
    """
    Get a logger instance for logging.
    Args:
        filename (str): The name of the log file.
        task_id (str, optional): The ID of the task. Defaults to None.
    Returns:
        logging: The logger instance.
    """

    if task_id and filename:
        return logger(filename=filename, task_id=task_id)
    return logger(filename=KEY_PROJECT_NAME, task_id=KEY_PROJECT_NAME)
