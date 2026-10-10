from pages.contact_page import ContactPage
from pathlib import Path
import allure


PDF_FILE = Path(__file__).parents[2] / "files" / "test.pdf"


@allure.title("Contact form sends a message with a PDF file")
@allure.description("The user fills the contact form, uploads a PDF file and sends the message.")
def test_contact_form_with_file(page, user):
    contact_page = ContactPage(page)
    contact_page.open("/contact_us")

    contact_page.send_message(user["name"], user["email"], "Hello from the demo!", PDF_FILE)

    contact_page.should_see_success()
