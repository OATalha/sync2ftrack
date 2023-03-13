from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
import os
import sys
import time

import json


from ss_crawler.pages import MainPage, LoginPage, ProjectPage


syncsketch = "https://syncsketch.com"

minibods_syncsketch = "https://syncsketch.com/pro/#/project/195895"

with open("../credentials.json") as _cred:
    credentials = json.load(_cred)

review_id = "review_2451728"

os.environ["PATH"] += os.pathsep + os.path.abspath(
    f"../drivers/{sys.platform}"
)


def simple_login():
    driver = webdriver.Chrome()
    driver.get(syncsketch)
    main_page = MainPage(driver)
    main_page.click_login_button()
    login_page = LoginPage(driver)
    login_page.login(credentials["email"], credentials["password"])
    project_page = ProjectPage(driver)
    print(project_page.workspace_title.text)
    print(project_page.project_title.text)
    driver.close()


def load_project_page(driver) -> ProjectPage:
    driver.get(minibods_syncsketch)
    driver.maximize_window()

    login_page = LoginPage(driver)
    login_page.login(credentials["email"], credentials["password"])

    return ProjectPage(driver)


def list_reviews(driver):
    driver = webdriver.Chrome()

    project_page = load_project_page(driver)
    print(project_page.project_title.text)
    project_page.scroll_to_end()

    for review in project_page.get_reviews():
        print(review.get_name())

    review = project_page.get_review(id=review_id)
    print("\nSingle Review:")
    if review is not None:
        print(review.get_name())
        project_page.scroll_to_element(review.root_element)
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
    project_page = load_project_page(driver)
    project_page.scroll_to_end(max_scrolls=1)
    time.sleep(5)
    review = project_page.get_review(rid)
    if review is None:
        print("Review NOT Found!")
        return
    print(review.get_name())
    print('Attempting csv download ...')
    # review.download_csv()
    for ri in review.get_review_items():
        print((
            "Attempting ReviewItem Download - "
            "{order} ({type}): {name}"
            " -- {size}"
            " ...").format(**ri.get_data()))
        print('started download', ri.download_original())
    time.sleep(5)


def scroll_review(driver, rid: str = 'review_2462537'):
    project_page = load_project_page(driver)
    project_page.scroll_once()
    review = project_page.get_review(rid)
    if review is None:
        print("Review NOT Found!")
        return
    review.download_csv()
    count = 0
    for ri in review.get_review_items():
        count += 1
        ri.move_mouse_to()
        if count >= 10:
            break


if __name__ == "__main__":
    driver = webdriver.Chrome()
    download_review(driver, "review_2462537")
