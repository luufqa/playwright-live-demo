from playwright.sync_api import expect
from pages.base_page import BasePage
import allure


class HomePage(BasePage):
    @allure.step("Check home page is opened")
    def should_be_opened(self):
        expect(self.page).to_have_title("Automation Exercise")
        self.should_see_text("Features Items")
