# -*- encoding: utf-8 -*-
import sys
import json
import base64

from aimaestro.abcglobal.key import *
from aimaestro.taskflux.generateId.snowflake import snowflake_id

__all__ = [
    'load_config',
    'task_required_field_check'
]


def _blank_dictionary_value_processing(data: dict, key_name: str, is_bool: bool = False):
    """
    Process the value of a dictionary key_name.
    Args:
        data (dict): The dictionary containing the key_name-value pair.
        key_name (str): The key_name to process.
        is_bool (bool, optional): Indicates if the value should be treated as a boolean. Defaults to False.
    Returns:
        bool: True if the key_name exists in the dictionary and the value is not None or an empty string.
    """

    if key_name in data and data[key_name] is not None and data[key_name] != '':
        if is_bool is False:
            return True

        if type(data[key_name]) is str and data[key_name].lower() == 'true':
            return True

        if type(data[key_name]) is bool and data[key_name] is True:
            return True
    return False


def _config_default_value_processing(config: dict):
    """
    Process the default values in the configuration dictionary.
    Args:
        config (dict): The configuration dictionary.
    Returns:
        dict: The configuration dictionary with processed default values.
    """

    if KEY_ADMIN_USERNAME not in config:
        config[KEY_ADMIN_USERNAME] = DEFAULT_VALUE_USERNAME

    if KEY_ADMIN_PASSWORD not in config:
        config[KEY_ADMIN_PASSWORD] = DEFAULT_VALUE_PASSWORD

    if KEY_DEFAULT_SCHEDULE_TIME not in config:
        config[KEY_DEFAULT_SCHEDULE_TIME] = DEFAULT_VALUE_SCHEDULE_TIME

    return config


def task_required_field_check(message: dict):
    """
    Check if the required fields are present in the task message.
    Args:
        message (dict): The task message.
    Raises:
        Exception: If any of the required fields are missing.
    Returns:
        message (dict): The task message.
    """

    if _blank_dictionary_value_processing(data=message, key_name=KEY_TASK_ID) is False:
        message[KEY_TASK_ID] = snowflake_id()

    return message


def load_config(encoded_config):
    """
    Decode and load the encoded configuration string.

    Args:
        encoded_config (str): The encoded configuration string.

    Returns:
        dict: The decoded configuration dictionary.
    """
    try:
        encoded_bytes = encoded_config.encode('utf-8')
        decoded_bytes = base64.b64decode(encoded_bytes)
        decoded_string = decoded_bytes.decode('utf-8')
        return _config_default_value_processing(json.loads(decoded_string))
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)
