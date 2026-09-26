"""Actions Chexsa can perform inside the browser."""

from pathlib import Path
from typing import Any, Callable

from playwright.sync_api import Page


# BrowserActions asks BrowserState for the page that is currently open.
GetPageFn = Callable[[], Page]


class BrowserActions:
    """Perform browser actions chosen by the Agent/LLM."""

    def __init__(self, get_page: GetPageFn) -> None:
        self.get_page = get_page

    def execute(
        self,
        action: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Send an action name to the correct browser function."""

        actions = {
            "navigate": self.navigate,
            "click": self.click,
            "type": self.type_text,
            "scroll": self.scroll,
            "upload_file": self.upload_file,
        }

        if action not in actions:
            raise ValueError(f"Unknown browser action: {action}")

        return actions[action](**arguments)

    def navigate(self, url: str) -> str:
        """Open a URL in the current tab."""

        page = self.get_page()
        page.goto(url)

        return page.url

    def click(self, role: str, name: str) -> str:
        """Click an element using its ARIA role and visible name."""

        page = self.get_page()

        # Example: role="button", name="Apply"
        element = page.get_by_role(role, name=name).first
        element.click()

        return f'Clicked {role} "{name}"'

    def type_text(
        self,
        role: str,
        name: str,
        text: str,
    ) -> str:
        """Put text into an input found by its role and name."""

        page = self.get_page()

        # Example: role="textbox", name="Email"
        element = page.get_by_role(role, name=name).first
        element.fill(text)

        return f'Entered text into {role} "{name}"'

    def scroll(self, amount: int = 600) -> str:
        """Scroll the current page up or down."""

        page = self.get_page()

        # Positive scrolls down; negative scrolls up.
        page.mouse.wheel(0, amount)

        return f"Scrolled {amount} pixels"

    def upload_file(
        self,
        selector: str,
        file_path: str,
    ) -> str:
        """Upload a local file through a file input."""

        page = self.get_page()
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")

        page.locator(selector).set_input_files(str(path))

        return f"Uploaded {path.name}"
