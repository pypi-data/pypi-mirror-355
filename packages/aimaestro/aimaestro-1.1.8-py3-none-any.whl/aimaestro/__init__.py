# -*- encoding: utf-8 -*-
import time

from .taskflux import *

from .abcglobal import *
from .management import Management


class AiMaestro:

    def __init__(self, config_file: str, current_dir):
        GlobalVar(config_file=config_file, current_dir=current_dir)

        initialization_taskflux(config=GlobalVar().taskflux_config)

    @staticmethod
    def registry_services(services: list):
        services_registry(services=services)

    @staticmethod
    def start_management():
        Management(config=GlobalVar().taskflux_config).run()

    def start_services(self):
        services_start()
        time.sleep(10)
        self.start_management()
