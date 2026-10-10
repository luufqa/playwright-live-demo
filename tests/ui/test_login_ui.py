from pages.login_page import LoginPage
import allure
import pytest


@pytest.mark.integration
@allure.title("User created with the API can log in")
@allure.description("The fixture creates a user with the API. The user logs in with the UI.")
def test_login_with_api_user(page, user):
    login_page = LoginPage(page)
    login_page.open("/login")

    login_page.login(user["email"], user["password"])

    login_page.should_see_text(f"Logged in as {user['name']}")


@allure.title("Wrong password shows an error")
@allure.description("The user logs in with a wrong password and sees an error message.")
def test_login_with_wrong_password(page, user):
    login_page = LoginPage(page)
    login_page.open("/login")

    login_page.login(user["email"], "wrong-password")

    login_page.should_see_text("Your email or password is incorrect!")
