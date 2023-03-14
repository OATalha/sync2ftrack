import json
import os

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver


CRED_PATH = "../credentials.json"
CONF_PATH = "../config.json"


DRIVER = None


def get_chrome_driver() -> WebDriver:
    global DRIVER
    if DRIVER is None:
        chrome_options = webdriver.ChromeOptions()
        conf = get_config()
        prefs = {}
        if conf["download_location"]:
            prefs["download.default_directory"] = os.path.abspath(
                conf["download_location"]
            )
            chrome_options.add_experimental_option('prefs', prefs)
        DRIVER = webdriver.Chrome(chrome_options=chrome_options)
    return DRIVER


def get_credentials(path=os.path.abspath(CRED_PATH)):
    with open(path) as _cred:
        return json.load(_cred)


def get_config(path=os.path.abspath(CONF_PATH)):
    with open(path) as _conf:
        return json.load(_conf)


def get_download_location(conf_ath)
