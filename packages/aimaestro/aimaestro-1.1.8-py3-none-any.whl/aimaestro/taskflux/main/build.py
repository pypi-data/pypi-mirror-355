# -*- encoding: utf-8 -*-

import os
import sys
import inspect
import importlib
from typing import Union

from aimaestro.abcglobal.key import *
from aimaestro.plugins import initialization_mongo

from aimaestro.taskflux.ameta.abcmeta import ServiceConstructor, WorkerConstructor

from aimaestro.taskflux.rpc_proxy.decorator import rpc
from aimaestro.taskflux.utils.network import get_ipaddr
from aimaestro.taskflux.utils.timeformat import get_converted_time
from aimaestro.taskflux.logger.logger import initialization_logger, logger
from aimaestro.taskflux.queue.rabbitmq import initialization_rabbitmq
from aimaestro.taskflux.rpc_proxy.rpc_proxy import initialization_rpc_proxy
from aimaestro.taskflux.interface.interface import databases_send_message, databases_submit_task

__all__ = ['Build']


class Build:
    """
    Builds a worker by importing the specified class path and setting its attributes.
    """

    def __init__(self, config: dict, cls_path: str, build_type: str, constructor):
        self.config = config
        self.cls_path = cls_path
        self.build_type = build_type
        self.constructor = constructor

        initialization_logger(config)
        initialization_mongo(config)
        initialization_rabbitmq(config)
        initialization_rpc_proxy(config)

    def get_build_attr(self):
        """
        Imports the specified class path and returns its attributes.
        Returns:
            dict: A dictionary containing the attributes of the imported class.
        """
        if self.build_type == 'service':
            class_name = KEY_FUNCTION_RPC
        else:
            class_name = KEY_FUNCTION_WORKER

        script_path = os.path.dirname(self.cls_path)
        sys.path.insert(0, script_path)

        module_name, _file_extension = os.path.splitext(os.path.basename(self.cls_path))

        module = __import__(module_name, globals=globals(), locals=locals(), fromlist=[class_name])

        importlib.reload(module)
        cls = getattr(module, class_name)
        return cls.__dict__

    def build_functions(self, attrs):
        """
        Imports the specified class path and sets its attributes.
        """
        functions = {}
        for function_name in attrs:
            if function_name.startswith('__') is False:
                function = attrs[function_name]

                if type(function) in [type(lambda: None)]:
                    params = []
                    function = rpc(function)
                    signa = inspect.signature(function)
                    for name, param in signa.parameters.items():
                        if name != KEY_FUNCTION_SELF:
                            default_value = param.default
                            if param.default is inspect.Parameter.empty:
                                default_value = None

                            params.append({
                                KEY_FUNCTION_PARAM_NAME: name,
                                KEY_FUNCTION_PARAM_DEFAULT_VALUE: default_value
                            })

                    functions.setdefault(function_name, params)
                self.constructor.setattr(function_name, function)
        self.constructor.functions = functions

    def build(self, task_id: str = None) -> Union[ServiceConstructor, WorkerConstructor]:
        """
        Builds a worker by importing the specified class path and setting its attributes.
        Returns:
            ServiceConstructor: The constructed worker object.
        """
        attrs = self.get_build_attr()
        self.build_functions(attrs)

        self.constructor.submit_task = databases_submit_task
        self.constructor.send_message = databases_send_message

        self.constructor.worker_ipaddr = get_ipaddr()
        self.constructor.service_ipaddr = get_ipaddr()
        self.constructor.worker_version = get_converted_time()
        self.constructor.service_version = get_converted_time()
        self.constructor.worker_name = attrs.get(KEY_WORKER_NAME)
        self.constructor.service_name = attrs.get(KEY_SERVICE_NAME)

        if self.build_type == 'service':
            self.constructor.name = '{}_{}'.format(KEY_PROJECT_NAME, self.constructor.service_name)

            self.constructor.logger = logger(filename=KEY_PROJECT_NAME, task_id=self.constructor.service_name)
        else:
            self.constructor.name = '{}_{}'.format(KEY_PROJECT_NAME, self.constructor.worker_name)

            if task_id is None:
                self.constructor.logger = logger(filename=KEY_PROJECT_NAME, task_id=self.constructor.worker_name)
            else:
                self.constructor.logger = logger(filename=self.constructor.worker_name, task_id=task_id)

        return self.constructor
