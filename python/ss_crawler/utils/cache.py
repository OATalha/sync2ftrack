from fnmatch import fnmatch
import json
import os
import re
import shutil
import csv
from types import FunctionType
from typing import Literal, Optional, Union
from datetime import datetime
from zipfile import ZipFile

from ss_crawler.utils.filesize import FileSize


from ..conf import get_cache_location, DEFAULT_CONF_PATH


DATETIME_ARCHIVE_FORMAT = "%Y%m%d_%H%M%S_%f"
REVIEW_RE = r"^review_(\d+)$"
REVIEW_ITEM_RE = r"^item_(\d+)$"


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


class Cache(object):
    def __init__(self, conf: Optional[str] = None):
        if conf is None:
            conf = DEFAULT_CONF_PATH
        self._conf = conf

    @property
    def cache_base_dir(self):
        return get_cache_location(self._conf)


class ItemCache(Cache):
    cache_dir: str
    metadata_path: str

    def __init__(
        self, id: str, data: Optional[dict] = None, conf: Optional[str] = None
    ):
        super().__init__(conf)
        self._dirty = True
        self._id = id
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

    def _store_data(self, data: dict):
        self.create_directory()
        data["id"] = self._id
        metadata_path = self.metadata_path
        data = make_serializable(data)
        with open(metadata_path, "w+") as data_file:
            json.dump(data, data_file, indent=2)
        return metadata_path

    def _load_data(self) -> dict:
        data = {}
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path) as datafile:
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
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        if os.path.isfile(file_path):
            os.unlink(file_path)
        shutil.copy2(path, file_path)
        return file_path

    def has_file(self, pattern: str) -> str:
        if not os.path.isdir(self.cache_dir):
            return ""
        contents = os.listdir(self.cache_dir)
        for basename in contents:
            path = os.path.join(self.cache_dir, basename)
            if os.path.isfile(path):
                if fnmatch(basename, pattern):
                    return path
        return ""


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
    def metadata_path(self):
        return os.path.join(self.cache_dir, "review_metadata.json")

    def store_data(self):
        data = self._data.copy()
        data["review_items"] = self._review_items[:]
        datafile = self._store_data(data)
        self._dirty = False
        return datafile

    def load_data(self):
        data = self._load_data()
        if "review_items" in data:
            self._review_items = data["review_items"]
            del data["review_items"]
        self._data = data
        self._dirty = False

    @property
    def review_items(self):
        return self._review_items[:]

    def clear_review_items(self):
        self._review_items.clear()
        self._dirty = True

    def append_review_item(self, review_item_data: dict):
        self._review_items.append(review_item_data)
        self._dirty = True

    def get_num_notes(self) -> int:
        num_notes = 0
        csv_path = self.has_file("*.csv")
        if csv_path:
            with open(csv_path) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=",")
                for idx, _ in enumerate(csv_reader):
                    if idx == 0:
                        continue
                    num_notes += 1
        return num_notes

    def get_notes(self) -> list[dict]:
        notes = []
        csv_path = self.has_file("*.csv")
        if csv_path:
            with open(csv_path) as csv_file:
                csv_reader = csv.DictReader(csv_file, delimiter=",")
                for idx, row in enumerate(csv_reader):
                    if idx == 0:
                        continue
                    notes.append(row)
        return notes

    def get_num_sketches(self) -> int:
        num_sketches = 0
        zip_path = self.has_file("*.zip")
        if zip_path:
            with ZipFile(zip_path) as _zip:
                num_sketches = 0
                num_sketches = sum(
                    [
                        1
                        for fi in _zip.infolist()
                        if not fi.is_dir()
                        and os.path.splitext(fi.filename)[-1] == ".jpg"
                    ]
                )
        return num_sketches

    def get_sketches(self) -> list[str]:
        sketches = []
        zip_path = self.has_file("*.zip")
        sketch_dir = os.path.join(self.cache_dir, "sketches")
        if zip_path:
            with ZipFile(zip_path) as _zip:
                for file_info in _zip.infolist():
                    extract_path = os.path.join(sketch_dir, file_info.filename)
                    extract_dir = os.path.dirname(extract_path)
                    if not os.path.exists(extract_dir):
                        os.makedirs(extract_dir)
                    _zip.extract(file_info.filename, extract_path)
        return sketches

    def get_review_item_caches(self):
        return [
            ReviewItemCache(
                ridata["id"], ridata["review_id"], ridata, conf=self._conf
            )
            for ridata in self._review_items
        ]

    @property
    def needs_data_sync(self) -> bool:
        item_count = self._data.get("item_count")
        if item_count is None:
            return True
        return item_count != len(self._review_items)

    @property
    def needs_csv(self) -> bool:
        return not bool(self.has_file("*.csv"))

    @property
    def needs_zip(self) -> bool:
        return not bool(self.has_file("*.zip"))

    @property
    def needs_files(self) -> bool:
        return self.needs_zip or self.needs_csv

    @property
    def needs_media(self) -> bool:
        return any(
            [
                ri_cache.needs_download
                for ri_cache in self.get_review_item_caches()
            ]
        )

    @property
    def is_complete(self) -> bool:
        return not any(
            (
                self.needs_data_sync,
                self.needs_csv,
                self.needs_zip,
                self.needs_media,
            )
        )

    def remove(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
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
    def media_path(self):
        return os.path.join(self.cache_dir, self._data["name"])

    @property
    def metadata_path(self):
        return os.path.join(self.cache_dir, "review_item_metadata.json")

    @property
    def mtime(self) -> datetime:
        if os.path.exists(self.media_path):
            return datetime.fromtimestamp(os.path.getmtime(self.media_path))
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
        filename = self.media_path
        if os.path.exists(filename):
            os.unlink(filename)
        _dir = os.path.dirname(filename)
        if not os.path.exists(_dir):
            os.makedirs(_dir)
        shutil.copy2(path, self.media_path)
        return self.media_path


class CacheAnalytics(Cache):
    def get_reviews(self) -> list[ReviewCache]:
        base_dir = self.cache_base_dir
        content = os.listdir(base_dir)
        reviews = []
        for basename in content:
            review_path = os.path.join(base_dir, basename)
            if not (
                os.path.isdir(review_path)
                and (match := re.match(REVIEW_RE, basename))
            ):
                continue
            review_id = match.group(1)
            review_cache = ReviewCache(id=review_id)
            review_cache.load_data()
            reviews.append(review_cache)
        return reviews

    def filter_reviews(
        self,
        key: Union[
            Literal[
                "needs_data_sync",
                "needs_media",
                "needs_csv",
                "needs_zip",
                "needs_files",
                "is_complete",
            ],
            FunctionType,
        ],
        reviews: Optional[list[ReviewCache]] = None,
    ) -> list[ReviewCache]:
        if reviews is None:
            reviews = self.get_reviews()
        func = key
        if isinstance(key, str):

            def _get_review_prop(review) -> bool:
                return getattr(review, key)

            func = _get_review_prop
        return list(filter(func, reviews))  # type: ignore

    def get_candidate_reviews(
        self, top: int = 5
    ) -> list[ReviewCache]:
        reviews = self.filter_reviews(key="is_complete")
        reviews_ordered = sorted(
            reviews,
            key=lambda review: review.get_num_sketches(),
            reverse=True,
        )
        return reviews_ordered[:top]


def print_analytics():
    cache = CacheAnalytics()
    reviews = cache.get_reviews()
    print(len(cache.get_reviews()))
    print(len(cache.filter_reviews(key="needs_data_sync", reviews=reviews)))
    print(len(cache.filter_reviews(key="needs_media", reviews=reviews)))
    print(len(cache.filter_reviews(key="needs_zip", reviews=reviews)))
    print(len(cache.filter_reviews(key="needs_csv", reviews=reviews)))
    print(len(cache.filter_reviews(key="needs_files", reviews=reviews)))
    print(len(cache.filter_reviews(key="is_complete", reviews=reviews)))
