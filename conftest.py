from api.automation_exercise_api import AutomationExerciseApi
from playwright.sync_api import Playwright
from data.users import Users
import allure
import pytest


@pytest.fixture(scope="session")
def api(playwright: Playwright, base_url: str):
    """API client for the site. One client for all tests."""
    request = playwright.request.new_context(base_url=base_url)  # create a Playwright HTTP client for the site
    yield AutomationExerciseApi(request)  # give tests our class with API methods
    request.dispose()  # after all tests, close the client


@pytest.fixture(scope="session", autouse=True)
def user(api: AutomationExerciseApi):
    """Create a new user before all tests and delete this user after all tests."""
    user = Users.new_user()
    api.create_account(user)
    yield user
    api.delete_account(user["email"], user["password"])


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item):
    """After each failed UI test, add a screenshot to the Allure report."""
    report = yield
    page = item.funcargs.get("page")
    if report.when == "call" and report.failed and page:
        allure.attach(page.screenshot(full_page=True), name="Screenshot", attachment_type=allure.attachment_type.PNG)
    return report
