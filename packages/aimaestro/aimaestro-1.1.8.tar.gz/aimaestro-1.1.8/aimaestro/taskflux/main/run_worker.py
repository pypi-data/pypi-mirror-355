# -*- encoding: utf-8 -*-
import os
import sys
import time
import json
import argparse
import multiprocessing

from aimaestro.plugins import *
from aimaestro.abcglobal.key import *

from aimaestro.taskflux.ameta.abcmeta import WorkerConstructor

from aimaestro.taskflux.main.build import Build
from aimaestro.taskflux.utils.parser import load_config
from aimaestro.taskflux.logger.logger import initialization_logger
from aimaestro.taskflux.rpc_proxy.rpc_proxy import initialization_rpc_proxy
from aimaestro.taskflux.utils.timeformat import get_converted_time
from aimaestro.taskflux.queue.rabbitmq import receive_message, initialization_rabbitmq


class TaskRun:

    @staticmethod
    def run(cls_path: str, config: dict, body: dict):

        initialization_logger(config)
        initialization_mongo(config)
        initialization_rabbitmq(config)
        initialization_rpc_proxy(config)

        worker_pid = os.getpid()

        build = Build(
            config=config,
            cls_path=cls_path,
            build_type='worker',
            constructor=WorkerConstructor
        )
        constructor: WorkerConstructor = build.build(task_id=body[KEY_TASK_ID])

        start_ime = get_converted_time()
        task_insert_one(
            query={KEY_TASK_ID: body[KEY_TASK_ID]},
            data={
                KEY_WORKER_PID: worker_pid,
                KEY_WORKER_IPADDR: constructor.worker_ipaddr,
                KEY_TASK_STATUS: KEY_TASK_RUN_STATUS,
                KEY_TASK_START_TIME: start_ime
            }
        )

        worker_push_process(
            worker_name=constructor.worker_name,
            worker_ipaddr=constructor.worker_ipaddr,
            worker_pid=worker_pid
        )

        try:
            constructor().run(body)
            task_insert_one(
                query={KEY_TASK_ID: body[KEY_TASK_ID]},
                data={
                    KEY_WORKER_PID: os.getpid(),
                    KEY_WORKER_IPADDR: constructor.worker_ipaddr,
                    KEY_TASK_STATUS: KEY_TASK_SUCCESS_STATUS,
                    KEY_TASK_END_TIME: get_converted_time()
                }
            )
        except Exception as e:
            task_insert_one(
                query={KEY_TASK_ID: body[KEY_TASK_ID]},
                data={
                    KEY_WORKER_PID: os.getpid(),
                    KEY_WORKER_IPADDR: constructor.worker_ipaddr,
                    KEY_TASK_STATUS: KEY_TASK_ERROR_STATUS,
                    KEY_TASK_END_TIME: get_converted_time(),
                    KEY_TASK_ERROR_MESSAGE: str(e)
                }
            )

        worker_pull_process(
            worker_name=constructor.worker_name,
            worker_ipaddr=constructor.worker_ipaddr,
            worker_pid=worker_pid
        )


class RabbitmqCallback:
    """
    RabbitmqCallback is a class that represents a rabbitmq callback.
    It contains attributes such as name, config, logger, ip_addr,
     cls_path, rpc_proxy, database_tasks, and database_services.
    """

    config = None
    logger = None
    ip_addr = None
    cls_path = None
    worker_name = None

    def mq_callback(self, ch, method, properties, body):
        """
        Handles the callback for the rabbitmq message.
        Args:
            ch: The channel object.
            method: The method object.
            properties: The properties object.
            body: The body of the message.
        """
        ch.basic_ack(delivery_tag=method.delivery_tag)
        try:
            _body = json.loads(body.decode())
            if KEY_TASK_ID in _body:

                if KEY_SYSTEM_SERVICE_NAME not in self.worker_name:
                    status = query_task_status_by_task_id(task_id=_body.get(KEY_TASK_ID))
                else:
                    status = KEY_TASK_RUN_STATUS

                if status != KEY_TASK_STOP_STATUS:
                    run_worker, max_worker = query_worker_running_number(
                        query={
                            KEY_WORKER_NAME: self.worker_name,
                            KEY_SERVICE_IPADDR: self.ip_addr
                        }
                    )
                    if run_worker < max_worker:
                        multiprocessing.Process(target=TaskRun.run, args=(self.cls_path, self.config, _body,)).start()
                    else:
                        time.sleep(0.2)
                        ch.basic_publish(body=body, exchange='', routing_key=self.worker_name)
            else:
                self.logger.error('{} is not find, error data : {}'.format(KEY_TASK_ID, _body))
        except Exception as e:
            self.logger.error('mq_callback error: {}'.format(e))


class RunWorker:
    def __init__(self, config, cls_path):
        self.config = config
        self.cls_path = cls_path

    def worker_start(self):
        build = Build(
            config=self.config,
            cls_path=self.cls_path,
            build_type='worker',
            constructor=WorkerConstructor
        )
        constructor: WorkerConstructor = build.build(task_id=None)
        worker_data = {
            KEY_NAME: constructor.name,
            KEY_WORKER_IPADDR: constructor.worker_ipaddr,
            KEY_WORKER_NAME: constructor.worker_name,
            KEY_WORKER_VERSION: constructor.worker_version,
            KEY_WORKER_PID: os.getpid(),
            KEY_WORKER_FUNCTIONS: constructor.functions,
            KEY_WORKER_MAX_PROCESS: 10,
            KEY_WORKER_RUN_PROCESS: [],
        }

        service_insert_one(
            query={
                KEY_SERVICE_IPADDR: constructor.worker_ipaddr,
                KEY_SERVICE_NAME: constructor.worker_name
            },
            data=worker_data
        )
        constructor.logger.info('Worker started == {}'.format(worker_data))

        mq_callback = RabbitmqCallback()
        mq_callback.config = self.config
        mq_callback.cls_path = self.cls_path
        mq_callback.logger = constructor.logger
        mq_callback.ip_addr = constructor.worker_ipaddr
        mq_callback.worker_name = constructor.worker_name

        while True:
            try:
                receive_message(queue=constructor.worker_name, callback=mq_callback.mq_callback)
            except Exception as e:
                constructor.logger.error(' {} work error : {}'.format(constructor.worker_name, e))
            time.sleep(0.5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="run worker script")

    parser.add_argument("--config", type=str, help="worker config")
    parser.add_argument("--path", type=str, help="worker path")
    args = parser.parse_args()

    configs = load_config(args.config)

    sys.path.append(configs[KEY_ROOT_PATH])

    RunWorker(config=configs, cls_path=args.path).worker_start()
