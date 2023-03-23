from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver
from ss_crawler.exceptions import SSCrawlerException
from ss_crawler.pages import ProjectPage

from ss_crawler.scripts import ensure_project_page
from ss_crawler.utils.cache import ReviewCache, ReviewItemCache


def get_all_reviews(driver: WebDriver):
    project_page = ensure_project_page(driver)
    project_page.scroll_to_end()
    return [review.get_id() for review in project_page.get_reviews()]


def sync_review_data(driver: WebDriver, review_id: str):
    project_page = ensure_project_page(driver)
    print(f"Syncing data for review_{review_id}...")
    review = project_page.get_review(review_id)
    review_data = review.get_data()
    review_cache = ReviewCache(review_data["id"], data=review_data)
    for review_item in review.get_review_items():
        review_item_data = review_item.get_data()
        review_cache.append_review_item(review_item_data)


def sync_review_files(driver: WebDriver, review_id: str):
    print(f"Downoading files for review_{review_id}")
    project_page = ensure_project_page(driver)
    review = project_page.get_review(review_id)
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
            orig = review_item.download_original()
            orig_cache = review_item_cache.store_media(orig)
            print(f"Download file: {orig} - stored at {orig_cache}")


def sync_all_reviews(
    driver: WebDriver,
    review_data=False,
    review_files=False,
    review_media=False,
):
    if not any([review_data, review_files, review_media]):
        raise AttributeError("Must specify atleast one operation")
    review_ids = get_all_reviews(driver)
    my_handle = driver.current_window_handle
    to_sync = review_ids[:]
    while to_sync:
        to_sync, rids = [], to_sync
        print(f"Syncing data for {len(rids)} reviews ...")
        for idx, review_id in enumerate(rids):
            if (idx + 1) % 10 == 0:
                ProjectPage(driver).refresh()
            try:
                print(f"Syncing {idx+1} of {len(rids)} ...")
                if review_data:
                    sync_review_data(driver, review_id)
                if review_files:
                    sync_review_files(driver, review_id)
                if review_media:
                    sync_review_items_media(driver, review_id)
            except (SSCrawlerException, WebDriverException) as exc:
                print(f"review_{review_id} errored out with exception", exc)
                to_sync.append(review_id)
                driver.switch_to.window(my_handle)
                ProjectPage(driver).refresh()
        print(f"{len(to_sync)} errored out!")


def sync_all(driver: WebDriver):
    sync_all_reviews(driver, review_data=True)
    sync_all_reviews(driver, review_files=True)
    sync_all_reviews(driver, review_media=True)
