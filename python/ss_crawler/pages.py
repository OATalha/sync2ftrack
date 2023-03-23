from fnmatch import fnmatch
import os
import re
from typing import Optional, Any
import datetime

from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.expected_conditions import (
    presence_of_element_located,
)
from selenium.webdriver.support.wait import WebDriverWait

from ss_crawler.exceptions import (
    InvalidState,
    InvalidValue,
    UnknownValue,
    UnverifiedPage,
)


from .locators import (
    DownloadDialogLocators,
    MainPageLocators,
    LoginPageLocators,
    PageLocators,
    PopOverMenuLocators,
    ProjectPageLocators,
    ReviewItemLocators,
    ReviewLocators,
)


from .elements import (
    SimpleElement,
    SimpleSubPageElement,
    SubPageRootElement,
    WaitedElement,
    WaitedElements,
    WaitedSubPageElement,
    WaitedSubPageElements,
)


from .utils.download_management import DownloadManager
from .utils.filesize import FileSize


class Page(object):
    main_scroller = SimpleElement(PageLocators.BODY)

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.full_load = False
        if not self.verify():
            raise UnverifiedPage(
                f"{self.__class__.__name__} could not be verified"
            )

    def refresh(self):
        self.driver.get(self.driver.current_url)
        self.full_load = False

    @property
    def scroll_height(self):
        return int(self.main_scroller.get_attribute("scrollHeight"))

    @property
    def scroll_top(self):
        return int(self.main_scroller.get_attribute("scrollTop"))

    def verify(self) -> bool:
        return True

    def wait_until_scroll_height_changed(self, scroll_height, wait: int = 10):
        def scrollHeightChanged(_):
            currentScrollHeight = int(
                self.main_scroller.get_attribute("scrollHeight")
            )
            return currentScrollHeight != scroll_height

        try:
            WebDriverWait(self.driver, wait).until(scrollHeightChanged)
        except TimeoutException:
            self.full_load = True
            return False

        self.full_load = False
        return True

    def scroll_to(self, height: int):
        script = "arguments[0].scrollTo(0, arguments[1])"
        self.driver.execute_script(script, self.main_scroller, height)
        return self.scroll_top


class SubPage(Page):
    def __init__(self, parent_page: Page, root_element: WebElement):
        self.parent_page = parent_page
        self.root_element = root_element
        if not self.verify():
            raise UnverifiedPage(
                f"{self.__class__.__name__} could not be verified"
            )

    @property
    def driver(self) -> WebDriver:
        return self.parent_page.driver

    def move_mouse_to(self) -> bool:
        self.scroll_to_top()
        actions = ActionBuilder(self.driver)
        actions.pointer_action.move_to_location(*self.get_mid_point())
        actions.perform()
        return True

    def scroll_to_top(self):
        scroll_height = self.parent_page.scroll_height
        self.driver.execute_script(
            "arguments[0].scrollIntoView(true)", self.root_element
        )
        if not self.parent_page.full_load:
            self.parent_page.wait_until_scroll_height_changed(scroll_height)

    def scroll_to_view(self):
        scroll_height = self.parent_page.scroll_height
        self.driver.execute_script(
            "arguments[0].scrollIntoViewIfNeeded(true)", self.root_element
        )
        if not self.parent_page.full_load:
            self.parent_page.wait_until_scroll_height_changed(scroll_height)

    def get_rect(self) -> dict[str, float]:
        location = self.driver.execute_script(
            "return arguments[0].getBoundingClientRect();", self.root_element
        )
        return location

    def get_mid_point(self) -> tuple[int, int]:
        rect = self.get_rect()
        return (
            int(rect["x"] + rect["width"] / 2),
            int(rect["y"] + rect["height"] / 2),
        )


class MainPage(Page):
    login_button = SimpleElement(MainPageLocators.LOGIN_BUTTON)

    def verify(self) -> bool:
        return self.driver.title == "SyncSketch"

    def goto_login_page(self):
        self.login_button.click()


class LoginPage(Page):
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


class ProjectPage(Page):
    workspace_title = WaitedElement(
        ProjectPageLocators.WORKSPACE_NAME,
        condition=presence_of_element_located,
    )
    project_title = WaitedElement(
        ProjectPageLocators.PROJECT_NAME, condition=presence_of_element_located
    )
    main_scroller = WaitedElement(ProjectPageLocators.MAIN_SCROLLER)
    reviews = WaitedElements(ProjectPageLocators.REVIEW)

    def verify(self) -> bool:
        return bool(self.project_title.text)

    def scroll_once(self, wait: int = 5) -> bool:
        scroll_height = int(self.main_scroller.get_attribute("scrollHeight"))
        self.scroll_to(scroll_height)
        return self.wait_until_scroll_height_changed(scroll_height, wait)

    def scroll_to_end(self, max_scrolls: Optional[int] = None, wait: int = 5):
        counter = 0
        while self.scroll_once(wait):
            if max_scrolls is not None:
                counter += 1
                if counter >= max_scrolls:
                    break

    def get_reviews(self) -> list["Review"]:
        return [Review(self, element) for element in self.reviews]

    def get_review(
        self, id: Optional[str] = None, name: Optional[str] = None
    ) -> "Review":
        if id is None and name is None:
            raise TypeError("Please provide either 'id' or 'name'")
        while True:
            for review in self.get_reviews():
                if id is not None:
                    if fnmatch(review.get_id(), id):
                        return review
                elif name is not None:
                    if fnmatch(review.get_name(), name):
                        return review
            if not self.scroll_once():
                break
        raise UnknownValue(f"Cannot find review for id: {id} and name: {name}")


class ProjectSubPage(SubPage):
    def __init__(self, parent_page: ProjectPage, root_element: WebElement):
        self.parent_page = parent_page
        self.root_element = root_element
        if not self.verify():
            raise UnverifiedPage(
                f"{self.__class__.__name__} could not be verified"
            )


class Review(ProjectSubPage):
    expand_button = SimpleSubPageElement(ReviewLocators.EXPAND_BUTTON)
    download_button = WaitedSubPageElement(ReviewLocators.DL_BUTTON, 1)
    switch_button = WaitedSubPageElement(ReviewLocators.SWITCH_BUTTON)
    details_div = SimpleSubPageElement(ReviewLocators.DETAILS_DIV)
    details_table = WaitedSubPageElement(ReviewLocators.DETAILS_TABLE)
    details_grid = WaitedSubPageElement(ReviewLocators.DETAILS_GRID)
    review_items = WaitedSubPageElements(ReviewLocators.REVIEW_ITEM)
    item_count = SimpleSubPageElement(ReviewLocators.ITEM_COUNT)

    def get_id(self) -> str:
        id_string = self.root_element.get_dom_attribute("id")
        if match := re.match(r"^review_(\d+)$", id_string):
            return match.group(1)
        return id_string

    def get_name(self) -> str:
        review_name = self.root_element.find_element(
            *(ReviewLocators.REVIEW_NAME)
        )
        return review_name.text

    def get_item_count(self) -> int:
        return int(self.item_count.text)

    def get_project_title(self):
        return self.parent_page.project_title.text.strip()

    def get_workspace_title(self):
        return self.parent_page.workspace_title.text.strip()

    def get_data(self):
        return {
            "id": self.get_id(),
            "name": self.get_name(),
            "item_count": self.get_item_count(),
            "workspace": self.get_workspace_title(),
            "project": self.get_project_title(),
        }

    def is_expanded(self, _=None) -> bool:
        try:
            return self.details_div.is_displayed()
        except NoSuchElementException:
            return False

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
            except TimeoutException:
                return False
        return False

    def expand(self, wait: int = 1, max_tries: int = 10) -> bool:
        self.scroll_to_top()
        attempts = 0
        while True:
            try:
                if not self.is_expanded():
                    self.expand_button.click()
                WebDriverWait(self.driver, wait).until(self.is_expanded)
                break
            except TimeoutException:
                attempts += 1
                if attempts >= max_tries:
                    raise
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

    def show_details_table(self, wait: int = 1, max_tries: int = 5):
        self.expand()
        attempts = 0
        while True:
            try:
                if not self.has_details_table():
                    self.scroll_to_top()
                    self.switch_button.click()
                WebDriverWait(self.driver, wait).until(self.has_details_table)
                break
            except TimeoutException:
                attempts += 1
                if attempts >= max_tries:
                    raise
        return True

    def get_review_items(self):
        self.show_details_table()
        return [
            ReviewItem(self.parent_page, element)
            for element in self.review_items
        ]

    def request_download(self, text, max_tries: int = 10):
        attempts = 0
        while True:
            try:
                self.move_mouse_to()
                self.download_button.click()
                break
            except TimeoutException:
                attempts += 1
                if attempts >= max_tries:
                    raise
        menu = PopOverMenu(self.parent_page)
        item = menu.get_download_item_by_text(text)
        item.click()

    def download_csv(self, max_tries: int = 10):
        with DownloadManager(pattern="*.csv") as dm:
            self.request_download("*CSV", max_tries=max_tries)
        print(f"CSV File Downloaded: {dm.downloaded_file}")
        return dm.downloaded_file

    def download_sketches(self, wait: int = 3, max_tries: int = 10):
        self.request_download("*.Zip", max_tries=max_tries)
        diag = DownloadDialog(self.parent_page)
        attempts = 0
        while True:
            try:
                WebDriverWait(self.driver, wait).until(diag.download_ready)
                break
            except TimeoutException:
                attempts += 1
                if attempts >= max_tries:
                    raise
        with DownloadManager(pattern="*.zip") as dm:
            diag.begin_download()
        print(f"Zip File Downloaded: {dm.downloaded_file}")
        return dm.downloaded_file


class ReviewItem(ProjectSubPage):
    order_cell = SimpleSubPageElement(ReviewItemLocators.ORDER_CELL)
    name_cell = SimpleSubPageElement(ReviewItemLocators.NAME_CELL)
    by_cell = SimpleSubPageElement(ReviewItemLocators.BY_CELL)
    uploaded_cell = SimpleSubPageElement(ReviewItemLocators.UPLOADED_CELL)
    notes_cell = SimpleSubPageElement(ReviewItemLocators.NOTES_CELL)
    views_cell = SimpleSubPageElement(ReviewItemLocators.VIEWS_CELL)
    size_cell = SimpleSubPageElement(ReviewItemLocators.SIZE_CELL)
    type_cell = SimpleSubPageElement(ReviewItemLocators.TYPE_CELL)
    download_button = WaitedSubPageElement(ReviewItemLocators.DL_BUTTON, 1)

    def get_id(self) -> str:
        for _class in self.root_element.get_attribute("className").split():
            if match := re.match(r"^id_(\d+)$", _class):
                return match.group(1)
        raise InvalidState("Cannot get_id for review_item")

    def get_review_id(self) -> str:
        for _class in self.root_element.get_attribute("className").split():
            if match := re.match(r"^review_id_(\d+)$", _class):
                return match.group(1)
        raise InvalidState("Cannot get_id for review_item")

    def get_review(self):
        return self.parent_page.get_review(self.get_id())

    def get_order(self):
        try:
            return int(self.order_cell.text)
        except ValueError as exc:
            raise InvalidValue(*exc.args) from exc

    def get_name(self):
        return self.name_cell.get_dom_attribute("title")

    def get_views(self):
        return int(self.views_cell.text)

    def get_notes(self):
        return int(self.notes_cell.text)

    def get_size(self):
        return FileSize(self.size_cell.text)

    def get_type(self):
        return self.type_cell.text

    def get_user(self):
        return self.by_cell.text

    def get_upload_time(self):
        text = self.uploaded_cell.text
        return datetime.datetime.strptime(text, "%m/%d/%y %I:%M %p")

    def get_data(self) -> dict[str, Any]:
        return {
            "id": self.get_id(),
            "review_id": self.get_review_id(),
            "order": self.get_order(),
            "name": self.get_name(),
            "views": self.get_views(),
            "notes": self.get_notes(),
            "size": self.get_size(),
            "type": self.get_type(),
            "user": self.get_user(),
            "upload_time": self.get_upload_time(),
        }

    def initiate_download(self, text, max_tries=10):
        attempts = 0
        while True:
            try:
                self.move_mouse_to()
                self.download_button.click()
                break
            except TimeoutException:
                attempts += 1
                if attempts >= max_tries:
                    raise
        popovermenu = PopOverMenu(self.parent_page)
        item = popovermenu.get_download_item_by_text(text)
        item.click()

    def download_original(self, max_tries=2):
        item_text = "*Original*"
        _, ext = os.path.splitext(self.get_name())
        with DownloadManager(
            pattern=f"*{ext}",
            file_size=self.get_size(),
        ) as dm:
            self.initiate_download(item_text, max_tries=max_tries)
        return dm.downloaded_file

    def download_transcoded(self, max_tries=2):
        item_text = "*Transcoded*"
        _, ext = os.path.splitext(self.get_name().lower())
        with DownloadManager(pattern=f"*{ext}") as dm:
            self.initiate_download(item_text, max_tries=max_tries)
        print(f"{ext} Media Downloaded: {dm.downloaded_file}")
        return dm.downloaded_file


class PopOverMenu(SubPage):
    root_element = SubPageRootElement(PopOverMenuLocators.POPOVER)
    items = WaitedSubPageElements(PopOverMenuLocators.POPOVER_ITEM)

    def __init__(self, parent_page: Page):
        super().__init__(parent_page, None)  # type: ignore

    def verify(self) -> bool:
        try:
            return self.root_element.is_displayed()
        except TimeoutException:
            return False

    def get_download_item_by_text(self, match_text: str) -> WebElement:
        for element in self.items:
            try:
                item_name = element.find_element(
                    *(PopOverMenuLocators.POPOVER_DL_ITEM_NAME)
                ).text
            except NoSuchElementException:
                # Not a download item
                continue
            if fnmatch(item_name.strip(), match_text):
                return element
        raise NoSuchElementException(
            f"Cannot find download item with {match_text}"
        )


class DownloadDialog(SubPage):
    root_element = SubPageRootElement(DownloadDialogLocators.DIALOG)
    body = SimpleSubPageElement(DownloadDialogLocators.BODY)
    download_link = SimpleSubPageElement(DownloadDialogLocators.DOWNLOAD_LINK)

    def __init__(self, parent_page: Page):
        super().__init__(parent_page, None)  # type: ignore

    def download_ready(self, _) -> bool:
        if self.get_body_text().startswith("Ready"):
            return True
        return False

    def is_working(self, _):
        if "Please wait" in self.get_body_text():
            return True
        return False

    def get_body_text(self) -> str:
        return self.body.text.strip()

    def begin_download(self):
        self.download_link.click()
