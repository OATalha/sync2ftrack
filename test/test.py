import random
from selenium import webdriver
import os
import sys
import time

import json

from selenium.common.exceptions import TimeoutException


from ss_crawler.pages import MainPage, LoginPage, ProjectPage
from ss_crawler.scripts import load_project_page
from ss_crawler.sync import complete_sync, sync_from_cache, sync_project_data
from ss_crawler.utils.cache import ProjectCache
from ss_crawler.utils.credentials import get_credentials, get_project_id
from ss_crawler.utils.filesize import FileSize
from ss_crawler.utils.webdriver import (
    ChromeDriver,
    get_chrome_driver,
    get_download_location,
)
from ss_crawler.utils.download_management import remove_dir_contents


def test_download_review(driver, rid: str = "2479559"):
    with ChromeDriver() as driver:
        project_page = load_project_page(driver)
        review = project_page.get_review(rid)
        if review is None:
            print("Review NOT Found!")
            return
        print(review.get_name())
        print("Attempting csv download ...")
        csv = review.download_csv()
        assert os.path.exists(csv)
        print(f"CSV download successful! - ({csv})")
        print("Attempting sketches download ... ")
        sketch = review.download_sketches()
        print(f"Sketch download successful - ({sketch})")
        assert os.path.exists(sketch)
        for ri in review.get_review_items():
            print(
                (
                    "Attempting ReviewItem Download - "
                    "{order} ({type}): {name}"
                    " -- {size}"
                    " ..."
                ).format(**ri.get_data())
            )
            orig = ri.download_original()
            print(f"Media Download successful - ({orig})")


def scroll_review(driver, rid: str = "review_2462537"):
    project_page = ProjectPage(driver)
    project_page.scroll_once()
    review = project_page.get_review(rid)
    if review is None:
        print("Review NOT Found!")
        return
    review.download_csv()
    review.download_sketches()
    count = 0
    for ri in review.get_review_items():
        count += 1
        ri.move_mouse_to()
        if count >= 10:
            break


def test_complete_sync():
    # with ChromeDriver() as driver:
    #     sync_by_steps(driver)
    with ChromeDriver() as driver:
        complete_sync(driver)

def test_sync_from_cache():
    with ChromeDriver() as driver:
        sync_from_cache(driver)


def scroll_test():
    with ChromeDriver() as driver:
        project_page = load_project_page(driver)
        project_page.scroll_to_end()
        reviews = project_page.get_reviews()

        first = reviews[0]
        first.show_details_table()
        time.sleep(5)

        mid = reviews[int(len(reviews) / 2)]
        mid.show_details_table()
        time.sleep(5)

        last = reviews[-1]
        last.show_details_table()
        time.sleep(5)


def test_get_review():
    project_id = get_project_id()
    project_cache = ProjectCache(project_id)
    project_cache.load_data()
    review_caches = project_cache.get_reviews()
    with ChromeDriver() as driver:
        project_page = load_project_page(driver)
        for rc in random.choices(review_caches, k=5):
            review = project_page.get_review(rc._id)
            assert review.get_id() == rc._id
            print(review.get_data())
            for ri in review.get_review_items():
                print("\t", ri.get_data())


if __name__ == "__main__":
    test_sync_from_cache()
