"""Reads the current Chrome page for Chexsa.
It collects the URL, title, ARIA, visible text, and a screenshot."""

from dataclasses import dataclass
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
    screenshot: bytes
    changes: str


class BrowserState:
    """Connect to Chrome and read the current webpage."""

    def __init__(
        self,
        cdp_url: str = "http://127.0.0.1:9222",
        max_text_chars: int = 4000,
        max_aria_chars: int = 4000,
        max_changes_chars: int = 3000,
    ) -> None:
        self.cdp_url = cdp_url
        self.max_text_chars = max_text_chars
        self.max_aria_chars = max_aria_chars
        self.max_changes_chars = max_changes_chars
        self.previous_aria: str | None = None
        self.previous_text: str | None = None

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
        """Read the current browser state."""

        page = self.get_page()
        title = page.title()

        full_aria = self._read_aria(page)
        full_text = self._read_visible_text(page)

        aria = full_aria[: self.max_aria_chars]
        text = full_text[: self.max_text_chars]
        changes = self._get_changes(full_aria, full_text)
        screenshot = self._get_screenshot(page)

        self.previous_aria = full_aria
        self.previous_text = full_text

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
            screenshot=screenshot,
            changes=changes,
        )

    def get_page(self) -> Page:
        """Get the active tab from the connected Chrome instance."""

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

        # Prefer the tab the user is actually focused on.
        for page in pages:
            try:
                if page.evaluate("document.hasFocus()"):
                    self.active_page = page
                    return page
            except Exception:
                pass

        # If Chrome is not focused, the active tab is usually still visible.
        visible_pages = []

        for page in pages:
            try:
                if page.evaluate("document.visibilityState") == "visible":
                    visible_pages.append(page)
            except Exception:
                pass

        if len(visible_pages) == 1:
            self.active_page = visible_pages[0]
            return self.active_page

        if (
            self.active_page is not None
            and not self.active_page.is_closed()
            and self.active_page in pages
        ):
            return self.active_page

        self.active_page = pages[-1]
        return self.active_page

    def set_page(self, page: Page) -> None:
        """Set the tab Chexsa should currently use."""

        self.active_page = page

    def _read_aria(self, page: Page) -> str:
        """Read useful controls from the accessibility tree."""

        try:
            aria = page.locator("body").aria_snapshot()
        except Exception:
            return ""

        useful_lines = [
            line
            for line in aria.splitlines()
            if line.strip().startswith(
                tuple(f"- {role}" for role in ACTIONABLE_ARIA_ROLES)
            )
        ]

        return "\n".join(useful_lines)

    def _get_aria(self, page: Page) -> str:
        """Read useful controls with the normal context limit."""

        return self._read_aria(page)[: self.max_aria_chars]

    def _read_visible_text(self, page: Page) -> str:
        """Read visible page text."""

        try:
            return page.locator("body").inner_text()
        except Exception:
            return ""

    def _get_visible_text(self, page: Page) -> str:
        """Read visible text with the normal context limit."""

        return self._read_visible_text(page)[: self.max_text_chars]

    def _get_changes(self, aria: str, text: str) -> str:
        """Describe what changed since the previous browser state."""

        if self.previous_aria is None or self.previous_text is None:
            return "Initial page state."

        old_aria = set(self.previous_aria.splitlines())
        new_aria = set(aria.splitlines())
        old_text = set(self.previous_text.splitlines())
        new_text = set(text.splitlines())

        sections = []

        added_controls = [line for line in aria.splitlines() if line not in old_aria]
        removed_controls = [
            line for line in self.previous_aria.splitlines()
            if line not in new_aria
        ]
        added_text = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and line not in old_text
        ]
        removed_text = [
            line.strip()
            for line in self.previous_text.splitlines()
            if line.strip() and line not in new_text
        ]

        if added_text:
            sections.append("Added text:\n" + "\n".join(added_text))
        if added_controls:
            sections.append("Added controls:\n" + "\n".join(added_controls))
        if removed_controls:
            sections.append("Removed controls:\n" + "\n".join(removed_controls))
        if removed_text:
            sections.append("Removed text:\n" + "\n".join(removed_text))

        changes = "\n\n".join(sections) or "No visible changes."
        return changes[: self.max_changes_chars]

    def _get_screenshot(self, page: Page) -> bytes:
        """Capture the visible browser area."""

        screenshot = page.screenshot(
            type="jpeg",
            quality=50,
            full_page=False,
        )

        return screenshot

    def close(self) -> None:
        """Disconnect Chexsa from Chrome."""

        if self.browser is not None:
            self.browser.close()

        if self.playwright is not None:
            self.playwright.stop()
