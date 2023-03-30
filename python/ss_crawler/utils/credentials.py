import json
import os
import re

from ss_crawler import pages
from ss_crawler.exceptions import InvalidValue


CRED_PATH = os.path.abspath(os.path.expanduser("~/.ss_crawler/credentials.json"))


def get_credentials(path=CRED_PATH):
    with open(path) as _cred:
        return json.load(_cred)


def get_url(path=CRED_PATH):
    return get_credentials(path)["url"]


def get_email(path=CRED_PATH):
    return get_credentials(path)["email"]


def get_password(path=CRED_PATH):
    return get_credentials(path)["password"]


def get_project_id(path=CRED_PATH):
    url = get_url(path)
    if match := re.match(pages.ProjectPage.url_re, url):
        return match.group(2)
    raise InvalidValue("Credentials url does not have project id")
