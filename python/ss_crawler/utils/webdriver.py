import json
import os
import sys

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from . import download_management


def abspath(path):
    cur_dir = os.path.dirname(os.path.__file__)
    path = os.path.join(cur_dir, path)
    path = os.path.abspath(path)
    return path


CUR_DIR = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(CUR_DIR, "../../../"))


def qualify_path(path):
    return os.path.abspath(path.format(ROOT=ROOT, platform=sys.platform))


DEFAULT_CONF_PATH = qualify_path("{ROOT}/ss_crawler_config.json")


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


def get_config(path=DEFAULT_CONF_PATH):
    with open(path) as _conf:
        return json.load(_conf)


def get_download_location(path=DEFAULT_CONF_PATH) -> str:
    return qualify_path(get_config(path)["download_location"])


def get_cache_location(path=DEFAULT_CONF_PATH) -> str:
    return qualify_path(get_config(path)["cache_location"])


def chrome_driver_location(path=DEFAULT_CONF_PATH) -> str:
    return qualify_path(get_config(path)["chrome_driver"])


class ChromeDriver(object):
    def __init__(self, conf=DEFAULT_CONF_PATH, clear_downloads_dir=True):
        self.clear_downloads_dir = clear_downloads_dir
        self.conf = conf

    def __enter__(self):
        if self.clear_downloads_dir:
            download_management.remove_dir_contents(
                get_download_location(self.conf)
            )
        self.driver = get_chrome_driver(self.conf)
        return self.driver

    def __exit__(self, *_):  # exc_type, exc_val, traceback
        self.driver.quit()
