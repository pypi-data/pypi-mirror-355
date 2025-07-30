# -*- encoding: utf-8 -*-
import traceback

from aimaestro.taskflux import *


class RpcFunction(ServiceConstructor):
    """
    Class Name Not modifiable, Define RPC functions
    """
    service_name = 'web_automation'

    def get_service_name(self):
        return {"service_name": self.service_name}


class WorkerFunction(WorkerConstructor):
    """
    Class Name Not modifiable, Work Code
    """

    worker_name = 'web_automation'

    def run(self, data):
        primary_classification = data['primary_classification']
        secondary_classification = data['secondary_classification']

        try:

            if primary_classification == 'selenium_automation':
                from aimaestro.workflows.web_automation import selenium_automation

                selenium_automation.SeleniumAutomation(task=data, log_object=self.logger)

        except Exception as e:
            self.logger.error('{} - {}'.format(e, traceback.print_exc()))
