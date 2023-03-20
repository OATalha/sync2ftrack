import fnmatch
import json
import os
import re
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


class FileSize:
    UNITS = ["B", "KB", "MB", "GB"]
    BASE = 10
    UNIT_POWER = 3

    def __init__(self, size: Union[int, str]):
        if isinstance(size, str):
            self.value = self.parse_to_int(size)
        else:
            self.value = size

    def __int__(self):
        return self.value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"FileSize({self.value})"

    def __value__(self, other) -> int:
        if isinstance(other, FileSize):
            return other.value
        elif isinstance(other, str):
            return self.parse_to_int(other)
        else:
            return int(other)

    def __add__(self, other: Union["FileSize", int, str]):
        return FileSize(self.value + self.__value__(other))

    def humanized(self) -> str:
        return self.humanize(self.value)

    def is_valid(self) -> bool:
        return self.value >= 0

    @classmethod
    def unit_value(cls, unit: str):
        index = cls.UNITS.index(unit)
        return cls.BASE ** (index * cls.UNIT_POWER)

    @classmethod
    def size_pattern(cls):
        num_pattern = r"(?P<value>\d+(\.\d+))"
        tokens = "|".join([tok for tok in cls.UNITS])
        unit = rf"(?P<unit>{tokens})"
        return num_pattern + unit

    @classmethod
    def parse_to_int(cls, size_str: str) -> int:
        if match := re.match(cls.size_pattern(), size_str):
            value = float(match.group("value"))
            unit = match.group("unit")
            return int(value * cls.unit_value(unit))
        return int(size_str)

    @classmethod
    def humanize(cls, size: int):
        unit_factor = cls.BASE**cls.UNIT_POWER
        num = float(size)
        for unit in cls.UNITS[:-1]:
            if abs(num) < unit_factor:
                return f"{num:.1f}{unit}"
            num /= unit_factor
        return f"{num:.1f}{cls.UNITS[-1]}"


def discover_downloaded_file(
    file_pattern: str,
    file_size: Optional[FileSize] = None,
    download_location: Optional[str] = None,
    old_contents: Optional[set] = None,
    wait: float = 0,
    sleep: float = 1,
    partial_wait: float = 10,
) -> Union[str, None]:
    print("waiting for download", file_pattern)

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
        partial_files_found = []

        for _file in diff:
            if fnmatch.fnmatch(_file, "*.crdownload"):
                partial_files_found.append(_file)
                download_started = True

            if fnmatch.fnmatchcase(_file, file_pattern):
                match_found = True
                file_found = _file

        if partial_files_found and file_size is not None:
            partial_file = partial_files_found[0]
            size = FileSize(os.path.getsize(
                os.path.join(download_location, partial_file)
            ))
            print((
                f"{size.value/file_size.value * 100:.02f}% downloaded! - "
                f"({size.humanized()} of {file_size.humanized()})"
            ))
        if not partial_files_found:
            if download_started:
                download_started = False
                partial_wait = elapsed + 1.0
            if elapsed > partial_wait:
                raise DownloadNotDetected(
                    f"{elapsed}s but no partial files found"
                )

        if wait:
            if elapsed > wait:
                raise DownloadTimeout(f"Download timeout: {wait}s")

        time.sleep(sleep)

    if file_found is not None:
        return os.path.join(download_location, file_found)


class DownloadManager(object):
    def __init__(
        self,
        pattern: str = "*",
        file_size: Optional[FileSize] = None,
        download_location=None,
        wait: int = 0,
        sleep: float = 1,
        make_empty: bool = False,
    ):
        if download_location is None:
            download_location = get_download_location()
        self.download_location = download_location
        self.wait = wait
        self.pattern = pattern
        self.old_contents = set()
        self.sleep = sleep
        self.make_empty = make_empty
        self.file_size = file_size

    def __enter__(self):
        if self.make_empty:
            remove_dir_contents(self.download_location)
        if not os.path.exists(self.download_location):
            os.makedirs(self.download_location)
        self.old_contents = set(os.listdir(self.download_location))
        return self

    def __exit__(self, *_):
        self.downloaded_file = discover_downloaded_file(
            self.pattern,
            file_size=self.file_size,
            download_location=self.download_location,
            old_contents=self.old_contents,
            wait=self.wait,
            sleep=self.sleep,
        )
