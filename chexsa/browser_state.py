"""Read the current state of Chrome for Chexsa."""

from dataclasses import dataclass

from playwright.sync_api import Browser, Page, Playwright, sync_playwright


@dataclass
class BrowserSnapshot:
    """A simple description of the page Chexsa can currently see."""

    url: str
    title: str
    aria: str
    text: str


class BrowserState:
    """Connect to Chrome and read the current webpage."""

    def __init__(
        self,
        cdp_url: str = "http://127.0.0.1:9222",
        max_text_chars: int = 8000,
    ) -> None:
        self.cdp_url = cdp_url
        self.max_text_chars = max_text_chars

        self.playwright: Playwright | None = None
        self.browser: Browser | None = None

    def connect(self) -> None:
        """Connect Playwright to a Chrome instance already running."""

        self.playwright = sync_playwright().start()

        # CDP lets us control the real Chrome session instead of opening a new one.
        self.browser = self.playwright.chromium.connect_over_cdp(
            self.cdp_url
        )

    def observe(self) -> BrowserSnapshot:
        """Return the state of the current browser page."""

        page = self.get_page()

        return BrowserSnapshot(
            url=page.url,
            title=page.title(),
            aria=self._get_aria(page),
            text=self._get_visible_text(page),
        )

    def get_page(self) -> Page:
        """Get the most recently opened page from Chrome."""

        if self.browser is None:
            raise RuntimeError(
                "Browser is not connected. Call connect() first."
            )

        contexts = self.browser.contexts

        if not contexts:
            raise RuntimeError("Chrome has no browser context.")

        pages = contexts[-1].pages

        if not pages:
            raise RuntimeError("Chrome has no open pages.")

        # For now we use the newest tab.
        return pages[-1]

    def _get_aria(self, page: Page) -> str:
        """Read the page in a form that describes buttons, links, inputs, etc."""

        try:
            return page.locator("body").aria_snapshot()
        except Exception:
            # Some pages may not expose useful accessibility information.
            return ""

    def _get_visible_text(self, page: Page) -> str:
        """Get readable page text as a fallback for the accessibility tree."""

        try:
            text = page.locator("body").inner_text()
        except Exception:
            return ""

        # Huge webpages would waste LLM context, so keep only part of the text.
        return text[: self.max_text_chars]

    def close(self) -> None:
        """Disconnect Chexsa from Chrome."""

        if self.browser is not None:
            self.browser.close()

        if self.playwright is not None:
            self.playwright.stop()
