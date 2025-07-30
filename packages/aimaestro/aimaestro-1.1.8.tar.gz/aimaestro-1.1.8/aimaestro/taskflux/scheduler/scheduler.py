# -*- encoding: utf-8 -*-

import time
import pytz
import pickle
from pymongo import MongoClient
from threading import Thread, Event
from datetime import datetime, timedelta

from aimaestro.abcglobal.key import *
from aimaestro.taskflux.logger.logger import initialization_logger, logger
from aimaestro.taskflux.scheduler.cronparser import CronParser

__all__ = [
    'initialization_scheduler',
    'scheduler_add_job',
    'scheduler_remove_job',
    'scheduler_start',
    'scheduler_stop'
]


def initialization_scheduler(config: dict):
    """
    Initialize the scheduler.
    :param config: The configuration dictionary.
    """
    Scheduler(config=config)


def scheduler_add_job(job_id, cron_str, func_object, timezone="UTC", args=None, kwargs=None):
    """
    Add a job to the scheduler.
    :param job_id: The ID of the job.
    :param cron_str: The cron string defining the schedule.
    :param func_object: The function object to execute.
    :param timezone: The timezone for the schedule.
    :param args: Additional arguments to pass to the function.
    :param kwargs: Additional keyword arguments to pass to the function.
    """
    Scheduler().add_job(job_id, cron_str, func_object, timezone, args, kwargs)


def scheduler_remove_job(job_id):
    """
    Remove a job from the scheduler.
    :param job_id: The ID of the job to remove.
    """
    Scheduler().remove_job(job_id)


def scheduler_start():
    """
    Start the scheduler.
    """
    Scheduler().start()


def scheduler_stop():
    """
    Stop the scheduler.
    """
    Scheduler().stop()


class Scheduler:
    _instance = None

    _db = None
    _jobs = None
    _locks = None
    _client = None
    _thread = None
    _running = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Scheduler, cls).__new__(cls)
            cls._instance.__initialize(*args, **kwargs)
        return cls._instance

    def __initialize(self, config: dict):
        initialization_logger(config=config)
        self.logger = logger(filename=KEY_PROJECT_NAME, task_id='scheduler')

        self._client = MongoClient(config[KEY_MONGO_CONFIG])
        self._db = self._client[KEY_PROJECT_NAME]
        self._jobs = self._db.scheduled_jobs
        self._locks = self._db.job_locks
        self._running = Event()
        self._thread = None

    def start(self):
        self._running.set()
        self._thread = Thread(target=self._run_loop)
        self._thread.start()

    def stop(self):
        self._running.clear()
        self._thread.join()

    def _run_loop(self):
        while self._running.is_set():
            now = datetime.now(pytz.utc)
            due_jobs = self._jobs.find({
                "enabled": True,
                "next_run_time": {"$lte": now}
            })
            for job in due_jobs:
                self._execute_job(job)
            time.sleep(1)

    def _execute_job(self, job):
        lock_expire = datetime.now(pytz.utc) + timedelta(seconds=30)
        lock_result = self._locks.update_one(
            {"job_id": job["_id"], "expire_at": {"$lt": datetime.now(pytz.utc)}},
            {"$set": {"expire_at": lock_expire}},
            upsert=True
        )
        if lock_result.modified_count > 0 or lock_result.upserted_id:
            try:
                func = pickle.loads(job["func"])
                Thread(target=self._run_task, args=(func, job)).start()

                cron_parser = CronParser(
                    cron_str=job["cron"],
                    timezone=job.get("timezone", "UTC")
                )
                next_run = cron_parser.get_next_run(datetime.now(pytz.utc))

                self._jobs.update_one(
                    {"_id": job["_id"]},
                    {"$set": {"next_run_time": next_run, "last_run_time": datetime.now(pytz.utc)}}
                )
            except Exception as e:
                self.logger.error(f"Task execution failed: {job['_id']} - {str(e)}")
            finally:
                self._locks.delete_one({"job_id": job["_id"]})

    def _run_task(self, func, job):
        try:
            func(*job["args"], **job["kwargs"])
        except Exception as e:
            self.logger.error(f"Task execution exception: {job['_id']} - {str(e)}")

    def add_job(self, job_id, cron_str, func_object, timezone="UTC", args=None, kwargs=None):
        existing_job = self._jobs.find_one({"_id": job_id})
        if existing_job:
            self.logger.warning(f"Job '{job_id}' already exists. Skipping insertion.")
            return

        cron_parser = CronParser(cron_str, timezone=timezone)
        next_run = cron_parser.get_next_run(datetime.now(pytz.utc))

        self._jobs.insert_one({
            "_id": job_id,
            "cron": cron_str,
            "func": pickle.dumps(func_object),
            "timezone": timezone,
            "args": args or [],
            "kwargs": kwargs or {},
            "enabled": True,
            "next_run_time": next_run,
            "last_run_time": None
        })

    def remove_job(self, job_id):
        self._jobs.delete_one({"_id": job_id})
