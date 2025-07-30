# -*- encoding: utf-8 -*-

import sys
import json
import time
import base64
import psutil
import subprocess
from pathlib import Path

from aimaestro.plugins import initialization_mongo

from aimaestro.taskflux.logger.logger import initialization_logger
from aimaestro.taskflux.queue.rabbitmq import initialization_rabbitmq
from aimaestro.taskflux.rpc_proxy.rpc_proxy import initialization_rpc_proxy
from aimaestro.taskflux.scheduler.scheduler import initialization_scheduler, scheduler_add_job, scheduler_start

__all__ = [
    'initialization_global_attr',
    'services_registry',
    'services_start'
]

_CONFIG = {}
_ENCODED_CONFIG = None
_SERVICE_LIST = []

_PYTHON_NAME = 'python'
_PYEXEC = sys.executable if 'python' in sys.executable else 'python3'


def _kill_process(script_file_path, target_file_path):
    """
    Kills the specified script file.
    Args:
        script_file_path : script file object
        target_file_path : target file object
    """

    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            name = proc.name()
            cmdline = proc.cmdline()
            if _PYTHON_NAME in name:
                script_file_path_proc = False
                target_file_path_proc = False
                for arg in cmdline:
                    if Path(script_file_path).as_posix() in Path(arg).as_posix():
                        script_file_path_proc = True

                    if Path(target_file_path).as_posix() in Path(arg).as_posix():
                        target_file_path_proc = True

                if script_file_path_proc and target_file_path_proc:
                    proc.kill()
                    time.sleep(0.1)
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue


def _start_server(service_main_file_path):
    """
    Starts the service and starts the heartbeat detection process.
    Args:
        service_main_file_path : The path to the service main file.
    Returns:
        int: The process ID of the newly started service process.
    """
    from aimaestro.taskflux.main import run_server
    script_file = Path(run_server.__file__).resolve()
    _kill_process(script_file_path=script_file, target_file_path=service_main_file_path)

    command = [
        _PYEXEC,
        script_file,
        '--config', _ENCODED_CONFIG,
        '--path', service_main_file_path
    ]

    process = subprocess.Popen(command)
    return process.pid


def _start_worker(service_main_file_path):
    """
    Starts the service and starts the heartbeat detection process.
    Args:
        service_main_file_path : The path to the service main file.
    Returns:
        int: The process ID of the newly started service process.
    """
    from aimaestro.taskflux.main import run_worker
    script_file = Path(run_worker.__file__).resolve()
    _kill_process(script_file_path=script_file, target_file_path=service_main_file_path)

    command = [
        _PYEXEC,
        script_file,
        '--config', _ENCODED_CONFIG,
        '--path', service_main_file_path
    ]
    process = subprocess.Popen(command)
    return process.pid


def _start_schedule():
    """
    Starts the schedule.
    Returns:
        int: The process ID of the newly started schedule process.
    """
    from aimaestro.taskflux.system_services.monitoring import SystemMonitoring
    from aimaestro.taskflux.system_services.task_distribution import TaskDistribution

    scheduler_add_job(
        job_id='system_monitoring',
        cron_str='0 0/1 * * * *',
        func_object=SystemMonitoring(config=_CONFIG).run
    )

    scheduler_add_job(
        job_id='task_distribution',
        cron_str='0/30 * * * * *',
        func_object=TaskDistribution(config=_CONFIG).run
    )
    scheduler_config = _CONFIG.get('scheduler')

    enable = True
    if scheduler_config:
        enable = scheduler_config.get('enable')

    if enable:
        scheduler_start()


def initialization_global_attr(config: dict):
    global _CONFIG, _ENCODED_CONFIG
    _CONFIG = config
    _ENCODED_CONFIG = base64.b64encode(json.dumps(config).encode('utf-8')).decode('utf-8')
    initialization_logger(config)
    initialization_mongo(config)
    initialization_rabbitmq(config)
    initialization_rpc_proxy(config)
    initialization_scheduler(config)


def services_registry(services: list):
    """
    Registers a list of services to be managed.

    Args:
        services (list): A list of services to be registered.
    """

    [_SERVICE_LIST.append(i) for i in services]


def services_start():
    """
    Starts the service management process. Currently, this method is a placeholder
    and does not perform any actions.
    """
    _start_schedule()

    from aimaestro.workflows.web_automation import web_automation
    _SERVICE_LIST.append(web_automation)

    for service in _SERVICE_LIST:
        service_main_file_path = Path(service.__file__).resolve()
        _start_server(service_main_file_path=service_main_file_path)
        _start_worker(service_main_file_path=service_main_file_path)
