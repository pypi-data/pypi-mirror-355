# -*- encoding: utf-8 -*-
from aimaestro.abcglobal.key import *
from aimaestro.taskflux.rpc_proxy.client import RpcClient

__all__ = ['initialization_rpc_proxy', 'remote_call', 'generate_unique', 'proxy_call']

_RPC_CONFIG = {
    KEY_RABBITMQ_URI: DEFAULT_VALUE_RABBITMQ_URI,
    KEY_RPC_CALL_TIMEOUT: DEFAULT_VALUE_RPC_CALL_TIMEOUT
}


def initialization_rpc_proxy(config: dict):
    """
    Initialize the logger with the given configuration.
    Args:
        config (dict): A dictionary containing the configuration.
    """
    global _RPC_CONFIG
    _RPC_CONFIG[KEY_RABBITMQ_URI] = config.get(KEY_RABBITMQ_CONFIG, DEFAULT_VALUE_RABBITMQ_URI)
    _RPC_CONFIG[KEY_RPC_CALL_TIMEOUT] = config.get(DEFAULT_VALUE_RPC_CALL_TIMEOUT, DEFAULT_VALUE_RPC_CALL_TIMEOUT)


def generate_unique():
    """
    Generates a unique identifier.
    Returns:
        str: The generated identifier.
    """
    client = RpcClient(config=_RPC_CONFIG)
    service_name = '{}_{}_{}'.format(KEY_PROJECT_NAME, KEY_SYSTEM_SERVICE_NAME, 'task_distribution')
    data = client.call(service_name=service_name, method_name='generate_id')
    return data


def remote_call(service_name: str, method_name: str, **params):
    """
    Makes a remote procedure call to the specified service and method with the given parameters.

    Args:
        service_name (str): The name of the service to call.
        method_name (str): The name of the method to call.
        **params: Arbitrary keyword arguments to pass to the method.

    Returns:
        Any: The result of the remote procedure call.
    """
    client = RpcClient(config=_RPC_CONFIG)
    data = client.call(
        service_name=service_name,
        method_name=method_name,
        **params
    )
    return data


def proxy_call(service_name: str, method_name: str, **params):
    """
    Makes a remote procedure call to the specified service and method with the given parameters.

    Args:
        service_name (str): The name of the service to call.
        method_name (str): The name of the method to call.
        **params: Arbitrary keyword arguments to pass to the method.

    Returns:
        Any: The result of the remote procedure call.
    """
    client = RpcClient(config=_RPC_CONFIG)
    _name = '{}_{}'.format(KEY_PROJECT_NAME, service_name)

    data = client.call(
        service_name=_name,
        method_name=method_name,
        **params
    )
    return data
