from locators.login_locators import LoginLocators
from pages.base_page import BasePage
import allure


class LoginPage(BasePage):
    @allure.step("Log in as '{email}'")
    def login(self, email: str, password: str):
        self.page.locator(LoginLocators.EMAIL).fill(email)
        self.page.locator(LoginLocators.PASSWORD).fill(password)
        self.page.locator(LoginLocators.LOGIN_BUTTON).click()

    @allure.step("Check login page is opened")
    def should_be_opened(self):
        self.should_see_text("Login to your account")

    @allure.step("Check signup form is visible")
    def should_see_signup_form(self):
        self.should_see_text("New User Signup!")
