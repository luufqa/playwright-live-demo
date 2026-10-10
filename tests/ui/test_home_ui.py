from pages.home_page import HomePage
import allure
import pytest


@pytest.mark.smoke
@allure.title("Home page opens")
@allure.description("The home page opens and shows the products.")
def test_home_page_opens(page):
    home = HomePage(page)
    home.open("/")

    home.should_be_opened()
