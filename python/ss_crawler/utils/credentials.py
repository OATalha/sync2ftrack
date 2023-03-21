import json
import os


CRED_PATH = "~/.ss_crawler/credentials.json"


def get_credentials(path=os.path.abspath(os.path.expanduser(CRED_PATH))):
    global CRED_PATH
    if path != CRED_PATH:
        CRED_PATH = path
    with open(path) as _cred:
        return json.load(_cred)
