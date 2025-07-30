# -*- encoding: utf-8 -*-

import pika
import pickle
from functools import wraps

from aimaestro.abcglobal.key import *

__all__ = ['rpc', 'service_running']

_RPC_METHODS = {}
_AMQP_CONFIG = {KEY_RABBITMQ_URI: DEFAULT_VALUE_RABBITMQ_URI}


def _parse_config():
    """
    Parse the RabbitMQ configuration string to extract host, port, user and password.

    Returns:
        tuple: A tuple containing host (str), port (int), user (str) and password (str).
    """

    parts = _AMQP_CONFIG.get(KEY_RABBITMQ_URI).split('@')

    user_passwd = parts[0].split('//')[1]
    host_port = parts[1]

    user, passwd = user_passwd.split(':')
    host, port = host_port.split(':')

    return host, int(port), user, passwd


def _start_consumer(queue_name, service_instance):
    """
    Start a RabbitMQ consumer.
    Args:
        queue_name (str): The name of the queue to consume from.
        service_instance (function): The function to be called when a message is received.
    """
    host, port, user, passwd = _parse_config()
    credentials = pika.PlainCredentials(user, passwd)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=host, port=port, credentials=credentials, heartbeat=600)
    )
    channel = connection.channel()

    channel.queue_declare(
        queue=queue_name,
        durable=True,
        arguments={'x-ha-policy': 'all'}
    )
    channel.basic_qos(prefetch_count=100)

    def callback(ch, method_frame, props, body):
        response = None
        try:
            data = pickle.loads(body)
            method_name = data['method']
            args = data.get('args', [])
            kwargs = data.get('kwargs', {})

            if method_name not in _RPC_METHODS:
                raise AttributeError(f"Method {method_name} not registered as RPC")

            method = getattr(service_instance, method_name)
            result = method(*args, **kwargs)
            response = pickle.dumps({
                'status': 'success',
                'result': result
            })
        except Exception as e:
            response = pickle.dumps({
                'status': 'error',
                'exception': str(e),
                'type': type(e).__name__
            })
        finally:
            ch.basic_ack(method_frame.delivery_tag)
            ch.basic_publish(
                exchange='',
                routing_key=props.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=props.correlation_id,
                    delivery_mode=2
                ),
                body=response
            )

    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback,
        consumer_tag=f"{queue_name}_consumer"
    )

    channel.start_consuming()


def rpc(func):
    """
    Decorator for RPC functions.
    Args:
        func (function): The function to be decorated.
    Returns:
        function: The decorated function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    global _RPC_METHODS
    _RPC_METHODS.setdefault(func.__name__)

    wrapper._is_rpc_func = True
    return wrapper


def service_running(service_cls, config):
    """
    Start a RabbitMQ consumer.
    Args:
        config (dict): The AMQP URL for the RabbitMQ server.
        service_cls (class): The function to be called when a message is received.
    """
    global _AMQP_CONFIG
    _AMQP_CONFIG = config

    service_instance = service_cls()
    service_name = getattr(service_instance, 'name', service_cls.__name__)
    _start_consumer(service_name, service_instance)
