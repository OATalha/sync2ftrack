from typing import TYPE_CHECKING
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement


if TYPE_CHECKING:
    from .pages import BasePage, BaseSubPage


class SimpleElement(object):
    def __init__(self, locator: tuple[str, str]):
        self.locator = locator

    def __get__(self, obj: "BasePage", owner: type["BasePage"]) -> WebElement:
        element = obj.driver.find_element(*(self.locator))
        return element


class WaitedElement(SimpleElement):
    def __init__(self, locator: tuple[str, str], wait: int = 10):
        super().__init__(locator)
        self.wait = wait

    def __get__(self, obj: "BasePage", owner: type["BasePage"]) -> WebElement:
        element = WebDriverWait(obj.driver, self.wait).until(
            EC.visibility_of_element_located(self.locator)
        )
        return element


class WaitedElements(WaitedElement):
    def __get__(
        self, obj: "BasePage", owner: type["BasePage"]
    ) -> list[WebElement]:
        try:
            WebDriverWait(obj.driver, self.wait).until(
                EC.visibility_of_element_located(self.locator)
            )
        except TimeoutException:
            pass
        elements = obj.driver.find_elements(*(self.locator))
        return elements


class SimpleSubPageElement(SimpleElement):
    def __get__(
        self, obj: "BaseSubPage", owner: type["BaseSubPage"]
    ) -> WebElement:
        element = obj.root_element.find_element(*(self.locator))
        return element


class WaitedSubPageElement(WaitedElement):
    def __get__(
        self, obj: "BaseSubPage", owner: type["BaseSubPage"]
    ) -> WebElement:
        element = WebDriverWait(obj.root_element, self.wait).until(
            EC.visibility_of_element_located(self.locator)
        )
        return element


class WaitedSubPageElements(WaitedElement):
    def __get__(
        self, obj: "BaseSubPage", owner: type["BaseSubPage"]
    ) -> list[WebElement]:
        try:
            WebDriverWait(obj.root_element, self.wait).until(
                EC.visibility_of_element_located(self.locator)
            )
        except TimeoutException:
            pass
        elements = obj.root_element.find_elements(*(self.locator))
        return elements
