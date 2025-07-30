# -*- encoding: utf-8 -*-

import abc

from aimaestro.taskflux.logger.logger import logger
from aimaestro.taskflux.interface.interface import databases_send_message, databases_submit_task

__all__ = ['ServiceConstructor', 'WorkerConstructor']


class Meta(abc.ABC):

    @property
    @abc.abstractmethod
    def submit_task(self): ...

    @property
    @abc.abstractmethod
    def send_message(self): ...

    @property
    @abc.abstractmethod
    def logger(self): ...

    @property
    @abc.abstractmethod
    def name(self): ...


class ServiceMeta(Meta):

    @property
    @abc.abstractmethod
    def service_name(self): ...

    @property
    @abc.abstractmethod
    def service_version(self): ...

    @property
    @abc.abstractmethod
    def service_ipaddr(self): ...


class WorkerMeta(Meta):

    @property
    @abc.abstractmethod
    def worker_name(self): ...

    @property
    @abc.abstractmethod
    def worker_version(self): ...

    @property
    @abc.abstractmethod
    def worker_ipaddr(self): ...

    @abc.abstractmethod
    def run(self, data): ...


class ServiceConstructor(ServiceMeta):
    """
    ServiceConstructor is a class that represents a constructor for a service.
    It contains attributes such as name, logger, service_name, service_ipaddr, service_version, and functions.
    """
    functions: list = []
    name: str = None
    service_name: str = None
    service_ipaddr: str = None
    service_version: str = None

    logger: logger = None
    submit_task: databases_submit_task = None
    send_message: databases_send_message = None

    @classmethod
    def setattr(cls, name, value):
        setattr(cls, name, value)

    def __call__(self):
        return self


class WorkerConstructor(WorkerMeta):
    """
    WorkerConstructor is a class that represents a constructor for a worker.
    It contains attributes such as name, logger, worker_name, worker_ipaddr, worker_version, and functions.
    It also contains a method called run, which takes in a body and runs the worker with the given body.
    """
    functions: list = []

    worker_name: str = None
    worker_ipaddr: str = None
    worker_version: str = None

    name: str = None
    logger: logger = None
    submit_task: databases_submit_task = None
    send_message: databases_send_message = None

    @classmethod
    def setattr(cls, name, value):
        setattr(cls, name, value)

    def run(self, body):
        """
        Runs the worker with the given body.
        Args:
            body (dict): The body of the worker.
        """

    def __call__(self):
        return self
