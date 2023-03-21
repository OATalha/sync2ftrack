import json
import os

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver


def abspath(path):
    cur_dir = os.path.dirname(os.path.__file__)
    path = os.path.join(cur_dir, path)
    path = os.path.abspath(path)
    return path


CUR_DIR = os.path.dirname(os.path.__file__)
ROOT = os.path.abspath(os.path.join(CUR_DIR, "../../../"))


def qualify_path(path):
    return os.path.abspath(path).format(ROOT=ROOT)


CONF_PATH = qualify_path("{ROOT}/ss_crawler_config.json")


def get_chrome_driver() -> WebDriver:
    chrome_options = webdriver.ChromeOptions()
    conf = get_config()
    prefs = {}
    if conf["download_location"]:
        prefs["download.default_directory"] = conf["download_location"]
        chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(
            executable_path=chrome_driver_location(),
            chrome_options=chrome_options)
    return driver


def get_config(path=CONF_PATH):
    with open(path) as _conf:
        return json.load(_conf)


def get_download_location(path=CONF_PATH) -> str:
    return qualify_path(get_config(path)["download_location"])


def get_cache_location(path=CONF_PATH) -> str:
    return qualify_path(get_config(path)["cache_location"])


def chrome_driver_location(path=CONF_PATH) -> str:
    return qualify_path(get_config(path)["chrome_driver"])


class ChromeDriver(object):
    def __init__(self):
        pass

    def __enter__(self):
        self.driver = get_chrome_driver()
        return self.driver

    def __exit__(self, exc_type, exc_val, traceback):
        self.driver.quit()
