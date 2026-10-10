from locators.products_locators import ProductsLocators
from playwright.sync_api import expect
from pages.base_page import BasePage
import allure


class ProductsPage(BasePage):
    @allure.step("Search product '{name}'")
    def search(self, name: str):
        self.placeholder_and_fill("Search Product", name)
        self.page.locator(ProductsLocators.SEARCH_BUTTON).click()

    @allure.step("Check every product name contains '{word}'")
    def should_show_only(self, word: str):
        names = self.page.locator(ProductsLocators.PRODUCT_NAME)
        expect(names.first).to_be_visible()
        for name in names.all_inner_texts():
            assert word.lower() in name.lower(), f"'{name}' does not contain '{word}'"
