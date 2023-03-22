import os
import sys
import json


CUR_DIR = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(CUR_DIR, "../../"))


def qualify_path(path):
    return os.path.abspath(path.format(ROOT=ROOT, PLATFORM=sys.platform))


DEFAULT_CONF_PATH = qualify_path("{ROOT}/ss_crawler_config.json")


def abspath(path):
    cur_dir = os.path.dirname(os.path.__file__)
    path = os.path.join(cur_dir, path)
    path = os.path.abspath(path)
    return path


def get_config(path=DEFAULT_CONF_PATH):
    with open(path) as _conf:
        return json.load(_conf)


def get_download_location(path=DEFAULT_CONF_PATH) -> str:
    return qualify_path(get_config(path)["download_location"])


def get_cache_location(path=DEFAULT_CONF_PATH) -> str:
    return qualify_path(get_config(path)["cache_location"])


def chrome_driver_location(path=DEFAULT_CONF_PATH) -> str:
    return qualify_path(get_config(path)["chrome_driver"])
