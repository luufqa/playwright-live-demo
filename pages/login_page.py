from locators.login_locators import LoginLocators
from pages.base_page import BasePage
import allure


class LoginPage(BasePage):
    @allure.step("Log in as '{email}'")
    def login(self, email: str, password: str):
        self.page.locator(LoginLocators.EMAIL).fill(email)
        self.page.locator(LoginLocators.PASSWORD).fill(password)
        self.page.locator(LoginLocators.LOGIN_BUTTON).click()
