from selenium.webdriver.common.by import By


class MainPageLocators(object):
    LOGIN_BUTTON = (By.LINK_TEXT, "Login")


class LoginPageLocators(object):
    LOGIN_FORM = (By.CSS_SELECTOR, "div.loginForm")
    EMAIL_FIELD = (By.CSS_SELECTOR, "input#id_email")
    PASSWORD_FIELD = (By.CSS_SELECTOR, "input#id_password")
    CONTINUE_BUTTON = (By.CSS_SELECTOR, "input#getStartedButton")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "input#getStartedButton")


class ProjectPageLocators(object):
    MAIN_SCROLLER = (By.ID, "main")
    PROJECT_NAME = (By.CSS_SELECTOR, "div.headerName>span")
    WORKSPACE_NAME = (By.CSS_SELECTOR,
                      "div.headerTitle>div.headerTitle__content")
    REVIEWS_CONTAINER = (By.CSS_SELECTOR, "section.items>div.reviews")
    REVIEW = (By.CSS_SELECTOR,
              "div.infinite-list>div.review.infinite-list-item")
    SEARCH_FIELD = (
            By.CSS_SELECTOR,
            "div.filterInput>input[type='text'][placeholder~='Search']")


class ReviewLocators(object):
    REVIEW_NAME = (By.CLASS_NAME, "item-name")
    DL_BUTTON = (By.CSS_SELECTOR, "i.ti-download")
    EXPAND_BUTTON = (By.CSS_SELECTOR, "div.badge[title^='Expand']")
    DETAILS_DIV = (By.CSS_SELECTOR, "div.details")
    DETAILS_TABLE = (By.CSS_SELECTOR, "div.details>div[id^='itemTable']")
    DETAILS_GRID = (By.CSS_SELECTOR, "div.details>div.itemListDiv")
    SWITCH_BUTTON = (By.CSS_SELECTOR, "div.switchIcons i")
    REVIEW_ITEM = (By.CSS_SELECTOR, "tr.el-table__row")


class ReviewItemLocators(object):
    ORDER_CELL = (By.CSS_SELECTOR,
                  "td.el-table__cell.handle-cell>div.cell>div")
    NAME_CELL = (By.CSS_SELECTOR, "td.el-table__cell div.name-text")
    VIEWS_CELL = (By.CSS_SELECTOR,
                  "td:nth-child(8).el-table__cell>div.cell>div")
    NOTES_CELL = (By.CSS_SELECTOR,
                  "td:nth-child(9).el-table__cell>div.cell>div")
    SIZE_CELL = (By.CSS_SELECTOR,
                 "td:nth-child(10).el-table__cell>div.cell")
    TYPE_CELL = (By.CSS_SELECTOR,
                 "td:nth-child(11).el-table__cell>div.cell")
    DL_BUTTON = (By.CSS_SELECTOR,
                 "td.el-table__cell button.ellipsis-button")


class PopOverMenuLocators(object):
    POPOVER = (By.CSS_SELECTOR, "div.popover")
    POPOVER_ITEM = (By.CSS_SELECTOR, "div.flex")
    POPOVER_DL_ITEM_NAME = (By.CSS_SELECTOR, "i.ti-download>span")
