import fnmatch
import json
import os
import time
from typing import Optional, Union
import shutil

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait


class DownloadException(Exception):
    pass


class DownloadTimeout(DownloadException):
    pass


class DownloadNotDetected(DownloadException):
    pass


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
            chrome_options.add_experimental_option("prefs", prefs)
        DRIVER = webdriver.Chrome(chrome_options=chrome_options)
    return DRIVER


def get_credentials(path=os.path.abspath(CRED_PATH)):
    global CRED_PATH
    if path != CRED_PATH:
        CRED_PATH = path
    with open(path) as _cred:
        return json.load(_cred)


def get_config(path=os.path.abspath(CONF_PATH)):
    global CONF_PATH
    if path != CONF_PATH:
        CONF_PATH = path
    with open(path) as _conf:
        return json.load(_conf)


def get_download_location() -> str:
    return os.path.abspath(get_config()["download_location"])


def get_cache_location() -> str:
    return os.path.abspath(get_config()["cache_location"])


def download_file_discovered(
    file_pattern: str,
    download_location: Optional[str] = None,
    old_contents: Optional[set] = None,
    wait: float = 0,
    sleep: float = 1,
    partial_wait: float = 10
) -> Union[str, None]:
    print('waiting for download', file_pattern)

    if download_location is None:
        download_location = get_download_location()

    if old_contents is None:
        old_contents = set(os.listdir(download_location))

    match_found = False
    file_found = None
    download_started = False

    start = time.perf_counter()

    if partial_wait < 1:
        partial_wait = 1

    while not match_found:
        new_contents = set(os.listdir(download_location))
        diff = new_contents - old_contents

        elapsed = time.perf_counter() - start
        partial_files_found = 0

        for _file in diff:

            if fnmatch.fnmatch(_file, '*.crdownload'):
                partial_files_found += 1
                download_started = True

            if fnmatch.fnmatchcase(_file, file_pattern):
                match_found = True
                file_found = _file

        print('elapsed:', elapsed,
              'partial:', partial_files_found,
              'initial_wait', partial_wait)

        if not partial_files_found:
            if download_started:
                download_started = False
                partial_wait = elapsed + 1.0
            if elapsed > partial_wait:
                raise DownloadNotDetected(
                        f"{elapsed}s but no partial files found")

        if wait:
            if elapsed > wait:
                raise DownloadTimeout(f"Download timeout: {wait}s")

        time.sleep(sleep)

    if file_found is not None:
        return os.path.join(download_location, file_found)


def remove_dir_contents(dirname: str) -> bool:
    if not os.path.exists(dirname):
        return True
    if os.path.isdir(dirname):
        for name in os.listdir(dirname):
            path = os.path.join(dirname, name)
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    os.unlink(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
            except Exception as e:
                return False
        return True
    return False


class DownloadManager(object):
    def __init__(
        self, pattern: str = "*", download_location=None, wait: int = 0,
        sleep: float = 1, make_empty: bool = False
    ):
        if download_location is None:
            download_location = get_download_location()
        self.download_location = download_location
        self.wait = wait
        self.pattern = pattern
        self.old_contents = set()
        self.sleep = sleep
        self.make_empty = make_empty

    def __enter__(self):
        if self.make_empty:
            remove_dir_contents(self.download_location)
        if not os.path.exists(self.download_location):
            os.makedirs(self.download_location)
        self.old_contents = set(os.listdir(self.download_location))
        return self

    def __exit__(self, *_):
        self.downloaded_file = download_file_discovered(self.pattern,
                                                        self.download_location,
                                                        self.old_contents,
                                                        self.wait,
                                                        self.sleep)
