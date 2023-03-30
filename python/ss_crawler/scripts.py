from typing import Optional
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from ss_crawler.exceptions import UnverifiedPage

from ss_crawler.pages import LoginPage, MainPage, ProjectPage, Review
from ss_crawler.utils.credentials import get_credentials
from ss_crawler.utils.filesize import FileSize
from ss_crawler.utils.webdriver import get_chrome_driver


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


def collect_file_sizes():
    driver = get_chrome_driver()
    project_page = load_project_page(driver)
    project_page.scroll_to_end()
    all_sizes = []
    # random.choices(project_page.get_reviews(), k=10):
    fs_acc = FileSize(0)
    review_ids = [r.get_id() for r in project_page.get_reviews()]
    total_reviews = len(review_ids)
    for i, _id in enumerate(review_ids):
        if i % 10 == 0:
            project_page.refresh()
        review = project_page.get_review(_id)
        if review is None:
            print("review not found")
            continue

        try:
            sizes = [item.get_size() for item in review.get_review_items()]
        except TimeoutException:
            continue

        for fs in sizes:
            fs_acc += fs
            print(
                f"review: {i+1} of {total_reviews}",
                "size: ",
                fs.humanized(),
                "acc:",
                fs_acc.humanized(),
            )
        all_sizes.extend(sizes)
    return all_sizes


def ensure_project_page(driver: WebDriver) -> ProjectPage:
    try:
        return ProjectPage(driver)
    except UnverifiedPage:
        return load_project_page(driver)


def get_all_reviews(driver: Optional[WebDriver] = None) -> list[Review]:
    if driver is None:
        driver = get_chrome_driver()
    project_page = ensure_project_page(driver)
    project_page.scroll_to_end()
    return project_page.get_reviews()
