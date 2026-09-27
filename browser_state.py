"""Reads the current Chrome page for Chexsa.
It collects the URL, title, ARIA structure, and visible text.
Temporary timers help us find slow browser-reading steps."""

from dataclasses import dataclass
from time import perf_counter

from playwright.sync_api import Browser, Page, Playwright, sync_playwright


ACTIONABLE_ARIA_ROLES = (
    "button",
    "link",
    "textbox",
    "searchbox",
    "combobox",
    "checkbox",
    "radio",
    "menuitem",
    "option",
    "tab",
    "heading",
)


@dataclass
class BrowserSnapshot:
    """A simple description of the page Chexsa can currently see."""

    url: str
    title: str
    aria: str
    text: str
    tabs: list[str]


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
        self.active_page: Page | None = None

    def connect(self) -> None:
        """Connect Playwright to a Chrome instance already running."""

        self.playwright = sync_playwright().start()

        # CDP connects Chexsa to the real Chrome session.
        self.browser = self.playwright.chromium.connect_over_cdp(
            self.cdp_url
        )

    def observe(self) -> BrowserSnapshot:
        """Read the current page and print how long each part takes."""

        total_start = perf_counter()
        page = self.get_page()

        # Measure how long reading the page title takes.
        title_start = perf_counter()
        title = page.title()
        print(f"[TIMER] Browser title: {perf_counter() - title_start:.2f}s")

        # Measure the two larger page-reading operations.
        aria = self._get_aria(page)
        text = self._get_visible_text(page)

        print(
            f"[TIMER] Browser observe total: "
            f"{perf_counter() - total_start:.2f}s"
        )

        tabs = [
            f"{index}: {tab.title()} | {tab.url}"
            for index, tab in enumerate(page.context.pages)
        ]

        return BrowserSnapshot(
            url=page.url,
            title=title,
            aria=aria,
            text=text,
            tabs=tabs,
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

        if self.active_page is not None and not self.active_page.is_closed():
            return self.active_page

        self.active_page = pages[-1]
        return self.active_page

    def set_page(self, page: Page) -> None:
        """Set the tab Chexsa should currently use."""

        self.active_page = page

    def _get_aria(self, page: Page) -> str:
        """Read useful interactive elements from the accessibility tree."""

        start = perf_counter()

        try:
            aria = page.locator("body").aria_snapshot()

            # Keep controls and headings the agent is likely to need.
            useful_lines = [
                line
                for line in aria.splitlines()
                if line.strip().startswith(
                    tuple(f"- {role}" for role in ACTIONABLE_ARIA_ROLES)
                )
            ]

            aria = "\n".join(useful_lines)

        except Exception:
            aria = ""

        print(f"[TIMER] Browser ARIA: {perf_counter() - start:.2f}s")
        return aria

    def _get_visible_text(self, page: Page) -> str:
        """Read visible page text and limit how much goes to the LLM."""

        start = perf_counter()

        try:
            text = page.locator("body").inner_text()
        except Exception:
            text = ""

        print(f"[TIMER] Browser text: {perf_counter() - start:.2f}s")

        # Limit large pages so they do not waste LLM context.
        return text[: self.max_text_chars]

    def close(self) -> None:
        """Disconnect Chexsa from Chrome."""

        if self.browser is not None:
            self.browser.close()

        if self.playwright is not None:
            self.playwright.stop()
