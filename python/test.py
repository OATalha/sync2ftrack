from selenium import webdriver
import os
import sys
import time

import json


from ss_crawler.pages import MainPage, LoginPage, ProjectPage
from webdriver_utils import get_chrome_driver, get_credentials


os.environ["PATH"] += os.pathsep + os.path.abspath(
    f"../drivers/{sys.platform}"
)

syncsketch = "https://syncsketch.com"


credentials = get_credentials()
minibods_syncsketch = credentials["url"]

review_id = "*2451728"


def simple_login():
    driver = webdriver.Chrome()
    driver.get(syncsketch)
    main_page = MainPage(driver)
    main_page.goto_login_page()
    login_page = LoginPage(driver)
    login_page.login(credentials["email"], credentials["password"])
    project_page = ProjectPage(driver)
    print(project_page.workspace_title.text)
    print(project_page.project_title.text)
    driver.close()


def load_project_page(driver) -> ProjectPage:
    driver.maximize_window()
    driver.get(credentials["url"])

    login_page = LoginPage(driver)
    login_page.login(credentials["email"], credentials["password"])

    return ProjectPage(driver)


def list_reviews(driver):
    project_page = load_project_page(driver)
    print(project_page.project_title.text)
    project_page.scroll_to_end()

    for review in project_page.get_reviews():
        print(review.get_name())

    review = project_page.get_review(id=review_id)
    print("\nSingle Review:")
    if review is not None:
        print(review.get_name())
        review.show_details_table()
        time.sleep(5)
        for ri in review.get_review_items():
            print(
                f"{ri.get_order()}: "
                f"{ri.get_name()}, "
                f"{ri.get_type()}, "
                f"{ri.get_size()}, "
                f"Notes: {ri.get_notes()}, "
                f"Views: {ri.get_views()}, "
            )
            ri.download_transcoded()
            time.sleep(5)

    time.sleep(100)


def download_review(driver, rid: str = "review_2479559"):
    project_page = ProjectPage(driver)
    project_page.scroll_to_end(max_scrolls=1)
    time.sleep(5)
    review = project_page.get_review(rid)
    if review is None:
        print("Review NOT Found!")
        return
    print(review.get_name())
    print("Attempting csv download ...")
    review.download_csv()
    print("Attempting sketches download ... ")
    review.download_sketches()
    for ri in review.get_review_items():
        print(
            (
                "Attempting ReviewItem Download - "
                "{order} ({type}): {name}"
                " -- {size}"
                " ..."
            ).format(**ri.get_data())
        )
        print("started download", ri.download_original())
    time.sleep(5)


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


def download_reviews():
    driver = get_chrome_driver()
    load_project_page(driver)
    download_review(driver, "*2473433")
    # download_review(driver, "review_2490864")
    download_review(driver, "*2462537")


if __name__ == "__main__":
    download_reviews()
