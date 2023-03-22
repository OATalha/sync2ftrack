import os
import shutil
import time
import fnmatch

from typing import Optional, Union

from .filesize import FileSize
from ..conf import get_download_location
from ..exceptions import DownloadTimeout, DownloadNotDetected


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
            except Exception:  # type: ignore
                return False
        return True
    return False


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
