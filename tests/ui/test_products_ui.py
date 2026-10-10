from pages.products_page import ProductsPage
import allure


@allure.title("Search shows only matching products")
@allure.description("The user searches 'jeans' and sees only products with 'jeans' in the name.")
def test_search_product_ui(page):
    products_page = ProductsPage(page)
    products_page.open("/products")

    products_page.search("jeans")

    products_page.should_see_text("Searched Products")
    products_page.should_show_only("jeans")
