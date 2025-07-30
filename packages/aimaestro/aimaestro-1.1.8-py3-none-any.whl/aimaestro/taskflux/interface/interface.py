# -*- encoding: utf-8 -*-

from aimaestro.abcglobal.key import *
from aimaestro.plugins import task_insert_one

from aimaestro.taskflux.queue.rabbitmq import send_message
from aimaestro.taskflux.utils.timeformat import get_converted_time
from aimaestro.taskflux.utils.parser import task_required_field_check

__all__ = ['databases_send_message', 'databases_submit_task', 'databases_create_subtask']


def databases_send_message(queue: str, message: dict, weight: int = DEFAULT_VALUE_TASK_WEIGHT) -> str:
    """
        Send a message to the queue.
        Args:
            queue (str): The name of the queue to send the message to.
            message (dict): The message to be sent.
            weight (int): The weight of the message. Default is 1.
        Returns:
            str: The task ID associated with the message.
        This method sends the provided message to the specified queue using the RabbitMQ instance.
    """
    message = task_required_field_check(message=message)
    body = {
        KEY_TASK_BODY: message,
        KEY_TASK_WEIGHT: weight,
        KEY_TASK_QUEUE_NAME: queue,
        KEY_TASK_IS_SUB_TASK: False,
        KEY_TASK_ID: message[KEY_TASK_ID],
        KEY_TASK_STATUS: KEY_TASK_SEND_STATUS,
        KEY_TASK_IS_SUB_TASK_ALL_FINISH: False,
        KEY_TASK_CREATE_TIME: get_converted_time()
    }

    task_insert_one(query={KEY_TASK_ID: body[KEY_TASK_ID]}, data=body)
    send_message(queue=queue, message=message)
    return message[KEY_TASK_ID]


def databases_submit_task(queue: str, message: dict, weight: int = DEFAULT_VALUE_TASK_WEIGHT) -> str:
    """
        Submit a task to the specified queue.
        Args:
            queue (str): The name of the queue to submit the task to.
            message (dict): The message to be submitted as a task.
            weight (int): The weight of the task. Default is 1.
        Returns:
            str: The task ID associated with the submitted task.
        This method submits the provided task to the specified queue using the RabbitMQ instance.
    """
    message = task_required_field_check(message=message)
    body = {
        KEY_TASK_BODY: message,
        KEY_TASK_WEIGHT: weight,
        KEY_TASK_QUEUE_NAME: queue,
        KEY_TASK_IS_SUB_TASK: False,
        KEY_TASK_ID: message[KEY_TASK_ID],
        KEY_TASK_STATUS: KEY_TASK_WAIT_STATUS,
        KEY_TASK_IS_SUB_TASK_ALL_FINISH: False,
        KEY_TASK_CREATE_TIME: get_converted_time()
    }

    task_insert_one(query={KEY_TASK_ID: body[KEY_TASK_ID]}, data=body)
    return message[KEY_TASK_ID]


def databases_create_subtask(source_task_id: str, subtask_queue: str, subtasks: list) -> list:
    """
        Create a subtask for the given task ID.
        Args:
            source_task_id (str): The ID of the task to create a subtask for.
            subtask_queue (str): The name of the queue to create the subtask in.
            subtasks (dict): The subtask to be created.
        Returns:
            str: The subtask ID associated with the created subtask.
        This method creates a subtask for the given task ID using the RabbitMQ instance.
    """
    subtask_ids = []
    for subtask in subtasks:
        message = task_required_field_check(message=subtask)
        message[KEY_TASK_SOURCE_ID] = source_task_id
        body = {
            KEY_TASK_BODY: message,
            KEY_TASK_WEIGHT: DEFAULT_VALUE_TASK_WEIGHT,
            KEY_TASK_QUEUE_NAME: subtask_queue,
            KEY_TASK_SOURCE_ID: source_task_id,
            KEY_TASK_IS_SUB_TASK: True,
            KEY_TASK_ID: message[KEY_TASK_ID],
            KEY_TASK_STATUS: KEY_TASK_WAIT_STATUS,
            KEY_TASK_IS_SUB_TASK_ALL_FINISH: False,
            KEY_TASK_CREATE_TIME: get_converted_time()
        }
        subtask_ids.append(message[KEY_TASK_ID])
        task_insert_one(query={KEY_TASK_ID: body[KEY_TASK_ID]}, data=body)
    return subtask_ids
