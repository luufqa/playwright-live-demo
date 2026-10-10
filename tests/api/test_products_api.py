import allure
import pytest


@pytest.mark.smoke
@allure.title("Products list returns products")
@allure.description("GET /api/productsList returns status 200 and a list of products.")
def test_products_list(api):
    status, body = api.get_products()

    assert status == 200
    assert len(body["products"]) > 0


@allure.title("Brands list returns brands")
@allure.description("GET /api/brandsList returns status 200 and a list of brands.")
def test_brands_list(api):
    status, body = api.get_brands()

    assert status == 200
    assert len(body["brands"]) > 0


@allure.title("Search finds products by name")
@allure.description("POST /api/searchProduct with 'jeans' returns only products with 'jeans' in the name.")
def test_search_product(api):
    status, body = api.search_product("jeans")

    assert status == 200
    assert all("jeans" in product["name"].lower() for product in body["products"])


@allure.title("Products list rejects POST with status 405")
@allure.description(
    "REST rule: an unsupported method must return HTTP 405. "
    "This test fails because the site returns HTTP 200 and puts 405 only in the body."
)
def test_products_list_rejects_post(api):
    status, body = api.post_products()

    assert body["message"] == "This request method is not supported."
    assert status == 405
