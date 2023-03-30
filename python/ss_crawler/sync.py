from typing import Optional
import collections
import os

from tqdm import tqdm

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver
from ss_crawler.exceptions import DownloadNotDetected, SSCrawlerException

from ss_crawler.scripts import (
    ensure_project_page,
    get_all_reviews,
    load_project_page,
)
from ss_crawler.utils.cache import ProjectCache, ReviewCache, ReviewItemCache
from ss_crawler.utils.credentials import get_project_id


def sync_project_data(driver: WebDriver) -> list[str]:
    print("Syncing review ids ...")
    project_page = load_project_page(driver)
    project_id = project_page.get_id()
    project_data = project_page.get_data()
    project_cache = ProjectCache(project_id)
    project_cache.data = project_data
    reviews = get_all_reviews(driver)
    total, new = 0, 0
    review_ids = []
    for idx in tqdm(range(0, len(reviews))):
        review = reviews[idx]
        total += 1
        review_data = review.get_data()
        review_id = review_data["id"]
        review_ids.append(review_id)
        review_cache = ReviewCache(review_id)
        if os.path.exists(review_cache.metadata_path):
            review_cache.load_data()
            _data = review_cache.data
            _data.update(review_data)
            review_cache.data = _data
        else:
            new += 1
        project_cache.append_review(review_data)
        review_cache.store_data()
    project_cache.store_data()
    print(
        f"Data for project_{project_id} synced! ..."
        f"\n\t... {new} of {total} reviews are new!"
    )
    return review_ids


def sync_review_data(driver: WebDriver, review_id: str):
    project_page = ensure_project_page(driver)
    print(f"Syncing data for review_{review_id}...")
    review = project_page.get_review(review_id)
    review_data = review.get_data()
    review_cache = ReviewCache(review_data["id"], data=review_data)
    for review_item in review.get_review_items():
        review_item_data = review_item.get_data()
        review_cache.append_review_item(review_item_data)
    review_cache.store_data()


def sync_review_files(driver: WebDriver, review_id: str):
    print(f"Downoading files for review_{review_id}")
    project_page = ensure_project_page(driver)
    review = project_page.get_review(review_id)
    print(f"found review {review.get_id()}")
    review_data = review.get_data()
    review_cache = ReviewCache(review_data["id"], data=review_data)
    csv = review.download_csv()
    csv_cache = review_cache.store_file(csv)
    print(f"Downloaded file: {csv}  - stored at {csv_cache}")
    sketch = review.download_sketches()
    sketch_cache = review_cache.store_file(sketch)
    print(f"Download file: {sketch} - stored at {sketch_cache}")


def sync_review_items_media(driver: WebDriver, review_id: str):
    project_page = ensure_project_page(driver)
    print(f"Downoading media for review_{review_id}")
    review = project_page.get_review(review_id)
    for review_item in review.get_review_items():
        review_item_data = review_item.get_data()
        review_item_cache = ReviewItemCache(
            review_item_data["id"],
            review_item_data["review_id"],
            review_item_data,
        )
        if review_item_cache.needs_download:
            try:
                media = review_item.download_original()
            except DownloadNotDetected:
                media = review_item.download_transcoded()
            media_cache = review_item_cache.store_media(media)
            review_item_cache.store_data()
            print(f"Download file: {media} - stored at {media_cache}")


def sync_review(
    driver: WebDriver,
    review_id: str,
    sync_data=True,
    sync_files=True,
    sync_media=True,
):
    if not any([sync_data, sync_files, sync_media]):
        raise AttributeError("Please specify atleast one operation")
    if sync_data:
        sync_review_data(driver, review_id)
    if sync_files:
        sync_review_files(driver, review_id)
    if sync_media:
        sync_review_items_media(driver, review_id)


def sync_reviews(
    driver: WebDriver,
    sync_data=False,
    sync_files=False,
    sync_media=False,
    review_ids: Optional[list[str]] = None,
    max_tries: int = 3,
):
    if not any([sync_data, sync_files, sync_media]):
        raise AttributeError("Must specify atleast one operation")
    project_page = ensure_project_page(driver)
    if review_ids is None:
        review_ids = sync_project_data(driver)
    my_handle = driver.current_window_handle
    to_sync = review_ids[:]
    tries = collections.defaultdict(int)
    while to_sync:
        to_sync, rids = [], to_sync
        print(f"Syncing for {len(rids)} reviews ...")
        for idx, review_id in enumerate(rids):
            if (idx + 1) % 10 == 0:
                project_page.refresh()
                project_page.scroll_to_end()
            try:
                print(f"Syncing {idx+1} of {len(rids)} ...")
                sync_review(
                    driver, review_id, sync_data, sync_files, sync_media
                )
            except (SSCrawlerException, WebDriverException) as exc:
                print(f"review_{review_id} errored with exception", exc)
                import traceback

                traceback.print_exc()
                tries[review_id] += 1
                if tries[review_id] < max_tries:
                    to_sync.append(review_id)
                driver.switch_to.window(my_handle)
                project_page.refresh()
                project_page.scroll_to_end()
        if to_sync:
            print(f"Trying {len(to_sync)} from those errored out!")


def sync_by_steps(
    driver: WebDriver,
    sync_data=False,
    sync_files=False,
    sync_media=False,
):
    if not any([sync_data, sync_files, sync_media]):
        raise AttributeError("Must specify atleast one operation")
    review_ids = sync_project_data(driver)
    if sync_data:
        sync_reviews(driver, sync_data=True, review_ids=review_ids)
    if sync_files:
        sync_reviews(driver, sync_files=True, review_ids=review_ids)
    if sync_media:
        sync_reviews(driver, sync_media=True, review_ids=review_ids)


def sync_from_cache(driver: WebDriver, refresh_ids=False):
    cache = ProjectCache(get_project_id())
    cache_reviews = cache.get_reviews()
    cache.filter_reviews
    sync_reviews(
        driver,
        sync_data=True,
        review_ids=[
            r._id
            for r in cache.filter_reviews(
                key="needs_data_sync", reviews=cache_reviews
            )
        ],
    )
    sync_reviews(
        driver,
        sync_files=True,
        review_ids=[
            r._id
            for r in cache.filter_reviews(
                key="needs_files", reviews=cache_reviews
            )
        ],
    )
    sync_reviews(
        driver,
        sync_media=True,
        review_ids=[
            r._id
            for r in cache.filter_reviews(
                key="needs_media", reviews=cache_reviews
            )
        ],
    )


def complete_sync(driver):
    sync_project_data(driver)
    sync_reviews(driver, sync_data=True, sync_files=True)
    sync_from_cache(driver)
