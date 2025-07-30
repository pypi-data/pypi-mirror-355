# -*- encoding: utf-8 -*-
import os
import time
from aimaestro.taskflux import *

from aimaestro.abcglobal import *
from aimaestro.plugins import SeleniumOperations


class SeleniumAutomation:

    def __init__(self, task, log_object):
        self.task = task
        self.log_object = log_object

        self.log_object.info(task)

        self.task_id = task['task_id']
        self.all_save_screenshot = task.get('all_save_screenshot')

        self.temporary_dir = os.path.join(ROOT_PATH, 'temporary_dir', 'web_automation', self.task_id)
        os.makedirs(self.temporary_dir, exist_ok=True)

        self.operations = SeleniumOperations(
            log_object=log_object,
            browser=task['browser'],
            wait_time=task['wait_time'],
            params=task['params'],
            width=task['width'],
            height=task['height']
        )
        self.run()

    def run(self):
        setup = 0

        assert_status = True
        for operation in self.task['operations']:
            if assert_status is False:
                break

            st = get_converted_time_float()

            describe = operation.get('describe')
            operation_type = operation.get('operation_type')
            value = operation.get('value')
            sleep = operation.get('sleep')
            locators = operation.get('locators')

            if operation_type == 'open_url':
                self.operations.open_url(url=value)
                self.log_object.info(f'Open url: {value}')

            if operation_type == 'save_screenshot':
                save_path = os.path.join(str(self.temporary_dir), f'{setup}.png')
                self.operations.save_screenshot(path=save_path)
                operation['screenshot_path'] = save_path

            if operation_type == 'input_text':
                element = self.operations.find_element(locators=locators)
                self.operations.input_text(element=element, keys=value)

            if operation_type == 'send_keys':
                element = self.operations.find_element(locators=locators)
                self.operations.send_keys(element=element, keys=value)

            if operation_type == 'click':
                element = self.operations.find_element(locators=locators)
                self.operations.click(element=element)

            if self.all_save_screenshot and operation_type != 'save_screenshot':
                save_path = os.path.join(str(self.temporary_dir), f'{setup}.png')
                self.operations.save_screenshot(path=save_path)

            time.sleep(sleep)
            if 'asserts' in operation:
                for _assert in operation['asserts']:
                    assert_type = _assert.get('assert_type')
                    assert_value = _assert.get('assert_value')
                    assert_locators = _assert.get('locators')

                    element_value = None
                    if assert_type == 'title':
                        element_value = self.operations.get_title()

                    if assert_type == 'text':
                        element = self.operations.find_element(locators=assert_locators)
                        element_value = element.text

                    if assert_type == 'selected':
                        element = self.operations.find_element(locators=assert_locators)
                        element_value = self.operations.assert_is_selected(element)

                    if assert_type == 'displayed':
                        element = self.operations.find_element(locators=assert_locators)
                        element_value = self.operations.assert_is_displayed(element)

                    if assert_type == 'attribute':
                        element = self.operations.find_element(locators=assert_locators)
                        expression = _assert.get('expression')
                        element_value = self.operations.get_attribute(element, attribute=expression)

                    if element_value != assert_value:
                        operation['assert_result'] = False
                        assert_status = False
                        self.log_object.info(f'[{describe}] assert failed')
                        break
                    else:
                        operation['assert_result'] = True

            et = get_converted_time_float()
            self.log_object.info(f'[{describe}] cost: {et - st}')
            setup += 1

        self.task['assert_status'] = assert_status
        self.log_object.info(self.task)
