# -*- encoding: utf-8 -*-

import os
import logging
from logging.handlers import TimedRotatingFileHandler

from aimaestro.abcglobal.key import *

__all__ = ['logger', 'initialization_logger']

_FMT = logging.Formatter(DEFAULT_VALUE_LOGS_FMT)
_SUFFIX = DEFAULT_VALUE_LOGS_SUFFIX

_LOGS_POOL = {}
_LOGS_FILE_PATH = os.path.expanduser("~")


def _get_log_file_path(filename: str, task_id: str = None):
    if task_id is None:
        return os.path.join(_LOGS_FILE_PATH, f'{filename}.log')
    else:
        os.makedirs(os.path.join(_LOGS_FILE_PATH, f'{filename}'), exist_ok=True)
        return os.path.join(_LOGS_FILE_PATH, filename, f'{task_id}.log')


def _get_logger(filename: str, task_id: str = None) -> logging:
    """
    Get a logger instance for logging messages.
    Args:
        filename (str): The name of the log file.
        task_id (str, optional): The ID of the task. Defaults to None.
    Returns:
        logging.Logger: A logger instance.
    """
    handler = _get_log_file_path(filename, task_id)
    if handler not in _LOGS_POOL:
        _logger = logging.getLogger(handler)
        _logger.setLevel(logging.INFO)
        _logger.propagate = False

        th = TimedRotatingFileHandler(filename=handler, when='MIDNIGHT', backupCount=7, encoding='utf-8')
        th.suffix = _SUFFIX
        th.setFormatter(_FMT)

        if not any(isinstance(h, logging.StreamHandler) for h in _logger.handlers):
            ch = logging.StreamHandler()
            ch.setFormatter(_FMT)
            _logger.addHandler(ch)

        _logger.addHandler(th)

        _LOGS_POOL[handler] = _logger
    return _LOGS_POOL[handler]


def initialization_logger(config: dict):
    """
    Initialize the logger with the given configuration.
    Args:
        config (dict): A dictionary containing the configuration.
    """
    global _LOGS_FILE_PATH
    _LOGS_FILE_PATH = os.path.join(config.get(KEY_ROOT_PATH), KEY_LOGS_PATH)


def logger(filename: str, task_id: str = None) -> logging.Logger:
    """
    Get a logger instance for logging messages.
    Args:
        filename (str): The name of the log file.
        task_id (str, optional): The ID of the task. Defaults to None.
    Returns:
        logging.Logger: A logger instance.
    """
    return _get_logger(filename, task_id)
