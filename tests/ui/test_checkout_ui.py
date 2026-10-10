import allure
import pytest


@pytest.mark.skip(reason="Real payments are not allowed in the demo")
@allure.title("User pays for the order with a real card")
@allure.description("This test is skipped on purpose: we never use real cards in tests.")
def test_checkout_with_real_card(page):
    page.goto("/payment")
