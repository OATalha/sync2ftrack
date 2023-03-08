from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import os
import sys
import time

import json


from ss_crawler.pages import MainPage, LoginPage, ProjectPage


syncsketch = 'https://syncsketch.com'

minibods_syncsketch = 'https://syncsketch.com/pro/#/project/195895'
with open('../credentials.json') as _cred:
    credentials = json.load(_cred)
review_id = 'review_2451728'

os.environ['PATH'] += os.pathsep + os.path.abspath(f'../drivers/{sys.platform}')


def simple_login():
    driver = webdriver.Chrome()
    driver.get(syncsketch)
    main_page = MainPage(driver)
    main_page.click_login_button()
    login_page = LoginPage(driver)
    login_page.login(credentials['email'], credentials['password'])
    project_page = ProjectPage(driver)
    print(project_page.workspace_title.text)
    print(project_page.project_title.text)
    driver.close()


def list_reviews():
    driver = webdriver.Chrome()
    driver.get(minibods_syncsketch)
    driver.maximize_window()

    login_page = LoginPage(driver)
    login_page.login(email, password)

    project_page = ProjectPage(driver)
    print(project_page.project_title.text)
    project_page.scroll_to_end()

    for review in project_page.get_reviews():
        print(review.get_name())

    review = project_page.get_review(id=review_id)
    print()
    print('got review', review.get_id())
    if review is not None:
        print(review.get_name())
        project_page.scroll_to_element(review.root_element)
        review.show_details_table()
        for ri in review.get_review_items():
            print(f'{ri.get_order()}: '
                  f'{ri.get_name()}, '
                  f'{ri.get_type()}, '
                  f'{ri.get_size()}, '
                  f'Notes: {ri.get_notes()}, '
                  f'Views: {ri.get_notes()}, '
                  )

    time.sleep(10)


if __name__ == '__main__':
    list_reviews()
