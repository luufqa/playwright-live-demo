from playwright.sync_api import APIRequestContext
import allure
import json


class AutomationExerciseApi:
    def __init__(self, request: APIRequestContext):
        self.request = request

    def send(self, method: str, url: str, form: dict = None, params: dict = None) -> tuple[int, dict]:
        """Send a request, add the response to the Allure report and return the status code and the JSON body."""
        response = self.request.fetch(url, method=method, form=form, params=params)
        body = json.loads(response.text())
        allure.attach(json.dumps(body, indent=2), name=f"{method} {url}", attachment_type=allure.attachment_type.JSON)
        return response.status, body

    @allure.step("Get all products")
    def get_products(self):
        return self.send("GET", "/api/productsList")

    @allure.step("Send POST to products list")
    def post_products(self):
        return self.send("POST", "/api/productsList")

    @allure.step("Get all brands")
    def get_brands(self):
        return self.send("GET", "/api/brandsList")

    @allure.step("Search product '{name}'")
    def search_product(self, name: str):
        return self.send("POST", "/api/searchProduct", form={"search_product": name})

    @allure.step("Create account")
    def create_account(self, user: dict):
        return self.send("POST", "/api/createAccount", form=user)

    @allure.step("Get user details by email")
    def get_user(self, email: str):
        return self.send("GET", "/api/getUserDetailByEmail", params={"email": email})

    @allure.step("Delete account")
    def delete_account(self, email: str, password: str):
        return self.send("DELETE", "/api/deleteAccount", form={"email": email, "password": password})
