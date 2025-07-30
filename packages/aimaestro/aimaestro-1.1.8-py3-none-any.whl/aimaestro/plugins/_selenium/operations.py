# -*- encoding: utf-8 -*-
import copy

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

__all__ = ["SeleniumOperations"]


class SeleniumOperations:

    def __init__(self, log_object, browser: str = 'chrome', wait_time: int = 30,
                 params: dict = None, width: int = 1920, height: int = 1080):
        self.log_object = log_object
        self.width = width
        self.height = height

        self.options = Options()

        if params is None or len(params) == 0:
            params = [
                '--headless',
                '--disable-gpu',
                '--lang=zh-CN.UTF-8',
                '--force-device-scale-factor=0.90'
            ]

        for p in params:
            self.options.add_argument(p)

        if browser == "chrome":
            self.driver = webdriver.Chrome(
                service=webdriver.ChromeService(
                    executable_path=ChromeDriverManager().install()
                ),
                options=self.options
            )
        if browser == 'firefox':
            self.driver = webdriver.Firefox(
                service=webdriver.FirefoxService(
                    executable_path=GeckoDriverManager().install()
                ),
                options=self.options
            )
        if browser == 'edge':
            self.driver = webdriver.Edge(
                service=webdriver.EdgeService(
                    executable_path=EdgeChromiumDriverManager().install()
                ),
                options=self.options
            )

        self.wait_time = wait_time
        self.driver.implicitly_wait(self.wait_time)

    @staticmethod
    def _get_keys(key: str):
        return getattr(Keys, key)

    def find_element(self, locators: list):
        """
        find element by locators
        :param locators: [{'Xpath': 'x'}, {'ID': '1'}, ...]
        :return: WebElement
        """
        original_implicit_wait = copy.deepcopy(self.wait_time)
        self.driver.implicitly_wait(1)

        try:
            by_value_pairs = []
            for locator in locators:
                locator_type = list(locator.keys())[0].upper()
                locator_value = list(locator.values())[0]
                by = getattr(By, locator_type)
                by_value_pairs.append((by, locator_value))

            def _any_locator_visible(driver):
                for _by, value in by_value_pairs:
                    try:
                        _element = driver.find_element(_by, value)
                        if _element.is_displayed():
                            return _element
                    except NoSuchElementException:
                        continue
                return False

            element = WebDriverWait(driver=self.driver, timeout=original_implicit_wait).until(_any_locator_visible)
            return element

        except TimeoutException:
            raise NoSuchElementException(f"all not find : {locators}")
        finally:
            self.driver.implicitly_wait(original_implicit_wait)

    def open_url(self, url: str):
        self.driver.get(url)
        self.driver.set_window_size(self.width, self.height)

    def save_screenshot(self, path: str):
        self.driver.save_screenshot(path)

    def send_keys(self, element, keys: str):
        element.send_keys(self._get_keys(keys))

    def get_title(self):
        return self.driver.title

    @staticmethod
    def get_attribute(element, attribute: str):
        return element.get_attribute(attribute)

    @staticmethod
    def input_text(element, keys: str):
        element.send_keys(keys)

    @staticmethod
    def click(element):
        element.click()

    @staticmethod
    def select(element, selector: str):
        element.select_by_value(selector)

    @staticmethod
    def assert_is_selected(element):
        return element.is_selected()

    @staticmethod
    def assert_is_displayed(element):
        return element.is_displayed()

    def close(self):
        self.driver.close()
