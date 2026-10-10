from uuid import uuid4


class Users:
    @staticmethod
    def new_user() -> dict:
        return {
            "name": "Demo User",
            "email": f"demo-{uuid4().hex[:8]}@example.com",
            "password": "Demo-12345",
            "firstname": "Demo",
            "lastname": "User",
            "address1": "1 Test Street",
            "country": "Canada",
            "state": "Ontario",
            "city": "Toronto",
            "zipcode": "10001",
            "mobile_number": "1234567890",
        }
