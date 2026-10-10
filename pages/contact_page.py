from locators.contact_locators import ContactLocators
from playwright.sync_api import Dialog, expect
from pages.base_page import BasePage
from pathlib import Path
import allure


class ContactPage(BasePage):
    @allure.step("Send message with a file")
    def send_message(self, name: str, email: str, message: str, file: Path):
        self.placeholder_and_fill("Name", name)
        self.placeholder_and_fill("Email", email)
        self.placeholder_and_fill("Subject", "Demo message")
        self.placeholder_and_fill("Your Message Here", message)
        self.page.locator(ContactLocators.FILE_INPUT).set_input_files(file)
        self.page.once("dialog", Dialog.accept)
        self.click_button("Submit")

    @allure.step("Check success message is visible")
    def should_see_success(self):
        expect(self.page.locator(ContactLocators.SUCCESS_MESSAGE)).to_have_text(
            "Success! Your details have been submitted successfully."
        )
