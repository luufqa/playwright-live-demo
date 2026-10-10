from playwright.sync_api import Page, expect


class BasePage:

    def __init__(self, page: Page):
        self.page = page

    def open(self, url: str):
        """Open the page by url. Do not wait for ads and other slow resources."""
        self.page.goto(url, wait_until="domcontentloaded")

    def click_button(self, name: str):
        """Click the button with this name."""
        self.page.get_by_role("button", name=name).click()

    def should_see_text(self, text: str):
        """Check that the text is visible."""
        expect(self.page.get_by_text(text)).to_be_visible()

    def placeholder_and_fill(self, placeholder: str, value: str):
        """Find the field by placeholder and fill it with the value."""
        self.page.get_by_placeholder(placeholder, exact=True).fill(value)
