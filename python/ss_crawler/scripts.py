from typing import Optional
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver
from ss_crawler.exceptions import SSCrawlerException

from ss_crawler.pages import LoginPage, MainPage, ProjectPage
from ss_crawler.utils.cache import ReviewCache, ReviewItemCache
from ss_crawler.utils.credentials import get_credentials
from ss_crawler.utils.webdriver import ChromeDriver, get_chrome_driver


SYNCSKETCH = "https://syncsketch.com"


def home_login(driver: WebDriver):
    driver.get(SYNCSKETCH)
    main_page = MainPage(driver)
    main_page.goto_login_page()
    login_page = LoginPage(driver)
    cred = get_credentials()
    login_page.login(cred["email"], cred["password"])
    return ProjectPage(driver)


def load_project_page(driver: Optional[WebDriver] = None):
    if driver is None:
        driver = get_chrome_driver()
    cred = get_credentials()
    driver.get(cred["url"])
    login_page = LoginPage(driver)
    login_page.login(cred["email"], cred["password"])
    return ProjectPage(driver)


def get_reviews(
    project_page: Optional[ProjectPage] = None,
    driver: Optional[WebDriver] = None,
):
    if project_page is None:
        if driver is None:
            driver = get_chrome_driver()
        project_page = load_project_page(driver)
    project_page.scroll_to_end()
    return project_page.get_reviews()


def ensure_project_page(driver: Optional[WebDriver] = None) -> ProjectPage:
    if driver is None:
        driver = get_chrome_driver()
    try:
        return ProjectPage(driver)
    except AssertionError:
        return load_project_page(driver)


def sync_reviews_data(driver: WebDriver) -> list[str]:
    reviews = get_reviews(driver=driver)
    review_ids = []
    print(f"Syncing review data for {len(reviews)} reviews ...")
    for review in reviews:
        review_id = review.get_id()
        review_cache = ReviewCache(review_id, data=review.get_data())
        review_cache.store_data()
        review_ids.append(review_id)
    print(f"Done syncing review data!")
    return review_ids


def sync_review_items_data(driver: WebDriver, review_id: str) -> str:
    project_page = ensure_project_page(driver)
    review = project_page.get_review(review_id)
    review_cache = ReviewCache(review_id)
    print(f"Syncing review item data for {review_id} ...")
    for review_item in review.get_review_items():
        if review_item.get_review_id() != review_id:
            print('Unexpected review id ... ignoring')
        review_cache.append_review_item(review.get_data())
    return review_cache.store_data()


def sync_review_files(driver, review_id):
    print(f"Downloading files for {review_id} ...")
    project_page = ensure_project_page(driver)
    review = project_page.get_review(review_id)
    review_cache = ReviewCache(review_id)
    csvfile = review.download_csv()
    review_cache.store_file(csvfile)
    sketchfile = review.download_sketches()
    review_cache.store_file(sketchfile)


def sync_review_items(driver: WebDriver, review_id: str):
    project_page = ensure_project_page(driver)
    review = project_page.get_review(id=review_id)
    rcache = ReviewCache(review.get_id())
    print(f"Downloading media for {review_id}")
    for review_item in review.get_review_items():
        review_item_id = review_item.get_id()
        parent_review_id = review_item.get_review_id()
        assert parent_review_id == review_id
        ri_cache = ReviewItemCache(
            review_item_id, review_id, data=review_item.get_data()
        )
        if ri_cache.needs_download:
            downloaded_file = review_item.download_original()
            ri_cache.store_media(downloaded_file)
            ri_cache.store_data()
        rcache.append_review_item(review_item.get_data())
    rcache.store_data()


def sync_all_data(driver: WebDriver):
    review_ids = sync_reviews_data(driver)
    project_page = ProjectPage(driver)

    for idx, rid in enumerate(review_ids):
        if idx % 10 == 0:
            project_page.refresh()
        try:
            sync_review_items_data(driver, rid)
        except (WebDriverException, SSCrawlerException) as exc:
            print(f"Error Encountered with review_{rid}", exc)
            continue

    for idx, rid in enumerate(review_ids):
        if idx % 10 == 0:
            project_page.refresh()
        try:
            sync_review_files(driver, rid)
        except (WebDriverException, SSCrawlerException) as exc:
            print(f"Error Encountered with review_{rid}", exc)
            continue

    for idx, rid in enumerate(review_ids):
        if idx % 10 == 0:
            project_page.refresh()
        try:
            sync_review_items(driver, rid)
        except (WebDriverException, SSCrawlerException) as exc:
            print(f"Error Encountered with review_{rid}", exc)
            continue
