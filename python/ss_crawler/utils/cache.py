import json
import os
import shutil
from typing import Optional
from datetime import datetime

from ss_crawler.utils.filesize import FileSize


from ..conf import get_cache_location, DEFAULT_CONF_PATH


DATETIME_ARCHIVE_FORMAT = "%Y%m%d_%H%M%S_%f"


def make_serializable(data: dict) -> dict:
    serializable = {}
    for key, value in data.items():
        svalue = value
        if isinstance(value, FileSize):
            svalue = int(value)
        elif isinstance(value, datetime):
            svalue = value.timestamp()
        elif isinstance(value, dict):
            svalue = make_serializable(value)
        elif isinstance(value, list):
            svalue = [make_serializable(item) for item in value]
        serializable[key] = svalue
    return serializable


def make_unserializable(data: dict) -> dict:
    rdict = {}
    for key, value in data.items():
        rvalue = value
        if key == "size":
            rvalue = FileSize(value)
        elif key == "upload_time":
            rvalue = datetime.fromtimestamp(value)
        elif isinstance(value, list):
            rvalue = [make_unserializable(item) for item in value]
        rdict[key] = rvalue
    return rdict


class ItemCache(object):
    cache_dir: str
    metadata_file: str

    def __init__(
        self, id: str, data: Optional[dict] = None, conf: Optional[str] = None
    ):
        self._dirty = True
        self._id = id
        if conf is None:
            conf = DEFAULT_CONF_PATH
        self._conf = conf
        self._data = {}
        if data is not None:
            self.data = data

    def get_dirty(self):
        return self._dirty

    def set_dirty(self, value: bool):
        self._dirty = value

    dirty = property(fset=set_dirty, fget=get_dirty)

    def get_data(self) -> dict:
        return self._data.copy()

    def set_data(self, data: dict):
        self._data = data.copy()
        self._dirty = True

    data = property(fset=set_data, fget=get_data)

    @property
    def cache_base_dir(self) -> str:
        return get_cache_location(self._conf)

    def _store_data(self, data: dict):
        self.create_directory()
        data["id"] = self._id
        metadata_file = self.metadata_file
        data = make_serializable(data)
        with open(metadata_file, "w+") as data_file:
            json.dump(data, data_file, indent=2)
        return metadata_file

    def _load_data(self) -> dict:
        data = {}
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file) as datafile:
                data = json.load(datafile)
        data = make_unserializable(data)
        return data

    def store_data(self):
        datafile = self._store_data(self._data.copy())
        self._dirty = False
        return datafile

    def load_data(self):
        self._data = self._load_data()
        self._dirty = False

    def create_directory(self):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        return self.cache_dir

    def store_file(self, path):
        _, ext = os.path.splitext(path)
        file_path = os.path.join(self.cache_dir, f"review_{self._id}{ext}")
        if os.path.isfile(file_path):
            os.unlink(file_path)
        shutil.copy2(path, file_path)
        return file_path


class ReviewCache(ItemCache):
    def __init__(
        self, id: str, data: Optional[dict] = None, conf: Optional[str] = None
    ):
        super().__init__(id, data, conf)
        self._review_items = []

    @property
    def cache_dir(self):
        return os.path.join(self.cache_base_dir, f"review_{self._id}")

    @property
    def metadata_file(self):
        return os.path.join(self.cache_dir, "review_metadata.json")

    def store_data(self):
        data = self._data.copy()
        data["review_items"] = self._review_items[:]
        datafile = self._store_data(data)
        self._dirty = False
        return datafile

    def load_data(self):
        data = self._load_data()
        self._review_items = data["review_items"]
        self._dirty = False

    @property
    def review_items(self):
        return self.review_items[:]

    def clear_review_items(self):
        self._review_items.clear()
        self._dirty = True

    def append_review_item(self, review_item_data: dict):
        self._review_items.append(review_item_data)
        self._dirty = True


class ReviewItemCache(ItemCache):
    def __init__(
        self,
        id: str,
        review_id: str,
        data: Optional[dict] = None,
        conf: Optional[str] = None,
    ):
        super().__init__(id, data, conf)
        self._review_id = review_id

    @property
    def cache_dir(self):
        return os.path.join(
            self.cache_base_dir,
            f"review_{self._review_id}",
            f"item_{self._id}",
        )

    @property
    def filename(self):
        return os.path.join(self.cache_dir, self._data["name"])

    @property
    def metadata_file(self):
        return os.path.join(self.cache_dir, "review_item_metadata.json")

    @property
    def mtime(self) -> datetime:
        if os.path.exists(self.filename):
            return datetime.fromtimestamp(os.path.getmtime(self.filename))
        return datetime.fromtimestamp(0)

    @property
    def upload_time(self) -> datetime:
        return self._data.get("upload_time", datetime.fromtimestamp(0))

    @property
    def needs_download(self) -> bool:
        return self.mtime < self.upload_time

    @property
    def archive_dir(self):
        return os.path.join(self.cache_dir, ".archive")

    def store_data(self):
        data = self._data.copy()
        data["review_id"] = self._review_id
        datafile = self._store_data(data)
        self._dirty = False
        return datafile

    def store_media(self, path):
        filename = self.filename
        if os.path.exists(filename):
            os.unlink(filename)
        _dir = os.path.dirname(filename)
        if not os.path.exists(_dir):
            os.makedirs(_dir)
        shutil.copy2(path, self.filename)
        return self.filename


# class CacheFile(object):
#     def __init__(self, name: Optional[str] = None, ext: Optional[str] = None):
#         self.name = name or ''
#         self.ext = ext or ''
#
#     def archive(self):
#         pass
#
#     def __get__(self, obj: "ItemCache", owner: type["ItemCache"]):
#         self.obj = obj
#         self.owner = owner
#         return self
#
#     def archive(self) -> str:
#         timestamp = self.mtime.strftime(DATETIME_ARCHIVE_FORMAT)
#         basename = self._data["name"]
#         archive_dir = os.path.join(self.archive_dir, timestamp)
#         archive_path = os.path.join(archive_dir, basename)
#         if os.path.exists(archive_path):
#             return archive_path
#         if not os.path.exists(archive_dir):
#             os.makedirs(archive_dir)
#         shutil.copy(self.filename, archive_path)
#         shutil.copy(self.metadata_file, archive_dir)
#         return archive_path
