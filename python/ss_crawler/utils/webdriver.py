from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from ..conf import (
    get_download_location,
    chrome_driver_location,
    DEFAULT_CONF_PATH,
)
from . import download_management


def get_chrome_driver(conf=DEFAULT_CONF_PATH) -> WebDriver:
    chrome_options = webdriver.ChromeOptions()
    prefs = {}
    prefs["download.default_directory"] = get_download_location(conf)
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(
        executable_path=chrome_driver_location(conf),
        chrome_options=chrome_options,
    )
    return driver


class ChromeDriver(object):
    def __init__(
        self, conf=DEFAULT_CONF_PATH, clear_downloads_dir=True, maximize=True
    ):
        self.clear_downloads_dir = clear_downloads_dir
        self.maximize = maximize
        self.conf = conf

    def __enter__(self) -> WebDriver:
        if self.clear_downloads_dir:
            download_management.remove_dir_contents(
                get_download_location(self.conf)
            )
        self.driver = get_chrome_driver(self.conf)
        if self.maximize:
            self.driver.maximize_window()
        return self.driver

    def __exit__(self, *_) -> bool:  # exc_type, exc_val, traceback
        self.driver.quit()
        return False
