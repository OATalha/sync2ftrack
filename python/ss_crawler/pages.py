from fnmatch import fnmatch
from typing import Optional

from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .locators import (
    MainPageLocators,
    LoginPageLocators,
    ProjectPageLocators,
    ReviewItemLocators,
    ReviewLocators,
)
from .elements import (
    SimpleElement,
    SimpleSubPageElement,
    WaitedElement,
    WaitedElements,
    WaitedSubPageElement,
    WaitedSubPageElements,
)


class BasePage(object):
    def __init__(self, driver: WebDriver):
        self.driver = driver
        assert self.verify()

    def verify(self) -> bool:
        return True


class BaseSubPage(BasePage):
    def __init__(self, driver: WebDriver, root_element: WebElement):
        self.driver = driver
        self.root_element = root_element


class MainPage(BasePage):
    login_button = SimpleElement(MainPageLocators.LOGIN_BUTTON)

    def verify(self) -> bool:
        return self.driver.title == "SyncSketch"

    def goto_login_page(self):
        self.login_button.click()


class LoginPage(BasePage):

    email_field = SimpleElement(LoginPageLocators.EMAIL_FIELD)
    password_field = WaitedElement(LoginPageLocators.PASSWORD_FIELD)
    continue_button = SimpleElement(LoginPageLocators.CONTINUE_BUTTON)
    login_button = WaitedElement(LoginPageLocators.LOGIN_BUTTON)

    def verify(self) -> bool:
        return self.driver.title.strip() == "Log In"

    def login(self, email, password):
        self.email_field.send_keys(email)
        self.continue_button.click()
        self.password_field.send_keys(password)
        self.login_button.click()


class ProjectPage(BasePage):
    workspace_title = WaitedElement(ProjectPageLocators.WORKSPACE_NAME)
    project_title = WaitedElement(ProjectPageLocators.PROJECT_NAME)
    main_scroller = WaitedElement(ProjectPageLocators.MAIN_SCROLLER)
    reviews = WaitedElements(ProjectPageLocators.REVIEW)

    def verify(self) -> bool:
        return bool(self.project_title.text)

    def scroll_to(self, scrollHeight: int):
        script = 'document.getElementById("{}").scrollTo(0, {})'.format(
            ProjectPageLocators.MAIN_SCROLLER[1], scrollHeight
        )
        self.driver.execute_script(script)

    def scroll_once(self, wait: int = 5) -> bool:
        scrollHeight = int(self.main_scroller.get_attribute("scrollHeight"))
        self.scroll_to(scrollHeight)

        def scrollHeightChanged(_):
            currentScrollHeight = int(
                self.main_scroller.get_attribute("scrollHeight")
            )
            return currentScrollHeight != scrollHeight

        try:
            WebDriverWait(self.driver, wait).until(scrollHeightChanged)
        except TimeoutException:
            return False

        return True

    def scroll_to_end(self, max_scrolls: Optional[int] = None, wait: int = 5):
        counter = 0
        while self.scroll_once(wait):
            if max_scrolls is not None:
                counter += 1
                if counter >= max_scrolls:
                    break

    def get_reviews(self) -> list["Review"]:
        return [Review(self.driver, element) for element in self.reviews]

    def get_review(
        self, id: Optional[str] = None, name: Optional[str] = None
    ) -> Optional["Review"]:
        if not any(x is None for x in [id, name]):
            raise ValueError("Please provide either 'id' or 'name'")
        for review in self.get_reviews():
            if id is not None:
                if fnmatch(review.get_id(), id):
                    return review
            elif name is not None:
                if fnmatch(review.get_name(), name):
                    return review

    def scroll_to_element(self, element: WebElement):
        re_top = int(element.get_attribute("offsetTop"))
        sc_top = int(self.main_scroller.get_attribute("offsetTop"))
        self.scroll_to(abs(re_top - sc_top))


class Review(BaseSubPage):
    expand_button = SimpleSubPageElement(ReviewLocators.EXPAND_BUTTON)
    download_button = WaitedSubPageElement(ReviewLocators.DL_BUTTON)
    switch_button = WaitedSubPageElement(ReviewLocators.SWITCH_BUTTON)
    details_div = SimpleSubPageElement(ReviewLocators.DETAILS_DIV)
    details_table = SimpleSubPageElement(ReviewLocators.DETAILS_TABLE)
    details_grid = SimpleSubPageElement(ReviewLocators.DETAILS_GRID)
    review_items = WaitedSubPageElements(ReviewLocators.REVIEW_ITEM)

    def get_id(self) -> str:
        return self.root_element.get_dom_attribute("id")

    def get_name(self) -> str:
        review_name = self.root_element.find_element(
            *(ReviewLocators.REVIEW_NAME)
        )
        return review_name.text

    def hover(self):
        actions = ActionChains(self.driver)
        actions.move_to_element(self.root_element)
        actions.perform()

    def is_expanded(self, _=None) -> bool:
        try:
            return self.details_div.is_displayed()
        except NoSuchElementException:
            return False
        return True

    def has_details_grid(self, _=None) -> bool:
        if self.is_expanded():
            try:
                return self.details_grid.is_displayed()
            except NoSuchElementException:
                return False
        return False

    def has_details_table(self, _=None) -> bool:
        if self.is_expanded():
            try:
                return self.details_table.is_displayed()
            except NoSuchElementException:
                return False
        return False

    def expand(self, wait: int = 1) -> bool:
        if not self.is_expanded():
            self.expand_button.click()
            try:
                WebDriverWait(self.driver, wait).until(self.is_expanded)
            except TimeoutException:
                return False
        return True

    def collapse(self, wait: int = 1):
        if self.is_expanded():
            self.expand_button.click()
            try:
                WebDriverWait(self.driver, wait).until(
                    lambda _: not self.is_expanded()
                )
            except TimeoutException:
                return False
        return True

    def show_details_table(self, wait: int = 5):
        self.expand()
        if not self.has_details_table():
            self.switch_button.click()
            print('switch requested!')
            try:
                WebDriverWait(self.driver, wait).until(self.has_details_table)
            except TimeoutException:
                return False
        return True

    def get_review_items(self):
        return [
            ReviewItem(self.driver, element) for element in self.review_items
        ]


class ReviewItem(BaseSubPage):
    order_cell = SimpleSubPageElement(ReviewItemLocators.ORDER_CELL)
    name_cell = SimpleSubPageElement(ReviewItemLocators.NAME_CELL)
    notes_cell = SimpleSubPageElement(ReviewItemLocators.NOTES_CELL)
    size_cell = SimpleSubPageElement(ReviewItemLocators.SIZE_CELL)
    type_cell = SimpleSubPageElement(ReviewItemLocators.TYPE_CELL)
    dl_button = SimpleSubPageElement(ReviewItemLocators.DL_BUTTON)

    def get_order(self):
        return int(self.order_cell.text)

    def get_name(self):
        return self.name_cell.get_dom_attribute("title")

    def get_notes(self):
        return int(self.notes_cell.text)

    def get_size(self):
        return self.size_cell.text

    def get_type(self):
        return self.type_cell.text


class PopOverMenu(BaseSubPage):
    pass
