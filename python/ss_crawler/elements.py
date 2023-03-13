from typing import TYPE_CHECKING, Union
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement


if TYPE_CHECKING:
    from .pages import Page, SubPage


class SimpleElement(object):
    def __init__(self, locator: tuple[str, str]):
        self.locator = locator

    def __get__(self, obj: "Page", owner: type["Page"]) -> WebElement:
        element = obj.driver.find_element(*(self.locator))
        return element


class WaitedElement(SimpleElement):
    def __init__(self, locator: tuple[str, str], wait: int = 10):
        super().__init__(locator)
        self.wait = wait

    def __get__(self, obj: "Page", owner: type["Page"]) -> WebElement:
        element = WebDriverWait(obj.driver, self.wait).until(
            EC.visibility_of_element_located(self.locator)
        )
        return element


class WaitedElements(WaitedElement):
    def __get__(
        self, obj: "Page", owner: type["Page"]
    ) -> list[WebElement]:
        try:
            WebDriverWait(obj.driver, self.wait).until(
                EC.presence_of_element_located(self.locator)
            )
        except TimeoutException:
            pass
        elements = obj.driver.find_elements(*(self.locator))
        return elements


class SimpleSubPageElement(SimpleElement):
    def __get__(
        self, obj: "SubPage", owner: type["SubPage"]
    ) -> WebElement:
        driver = obj.root_element or obj.driver
        element = driver.find_element(*(self.locator))
        return element


class WaitedSubPageElement(WaitedElement):
    def __get__(
        self, obj: "SubPage", owner: type["SubPage"]
    ) -> WebElement:
        driver = obj.root_element or obj.driver
        element = WebDriverWait(driver, self.wait).until(
            EC.visibility_of_element_located(self.locator)
        )
        return element


class SubPageRootElement(WaitedElement):
    def __set__(self, obj: "SubPage", value: Union[WebElement, None]):
        pass


class WaitedSubPageElements(WaitedElement):
    def __get__(
        self, obj: "SubPage", owner: type["SubPage"]
    ) -> list[WebElement]:
        driver = obj.root_element or obj.driver
        try:
            WebDriverWait(driver, self.wait).until(
                EC.presence_of_element_located(self.locator)
            )
        except TimeoutException:
            pass
        elements = driver.find_elements(*(self.locator))
        return elements
