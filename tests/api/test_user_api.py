import allure


@allure.title("User details return the created user")
@allure.description("The user from the fixture is created with the API. GET /api/getUserDetailByEmail finds this user.")
def test_user_details(api, user):
    status, body = api.get_user(user["email"])

    assert status == 200
    assert body["user"]["name"] == user["name"]
