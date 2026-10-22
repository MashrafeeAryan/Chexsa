"""Actions Chexsa can perform inside the browser."""

from pathlib import Path
from typing import Any, Callable

from playwright.sync_api import Locator, Page


GetPageFn = Callable[[], Page]
SetPageFn = Callable[[Page], None]
GetElementFn = Callable[[str], Locator]


class BrowserActions:
    """Perform browser actions chosen by the Agent/LLM."""

    def __init__(
        self,
        get_page: GetPageFn,
        set_page: SetPageFn,
        get_element: GetElementFn,
    ) -> None:
        self.get_page = get_page
        self.set_page = set_page
        self.get_element = get_element

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
            "press_key": self.press_key,
            "select_option": self.select_option,
            "check": self.check,
            "uncheck": self.uncheck,
            "go_back": self.go_back,
            "new_tab": self.new_tab,
            "close_tab": self.close_tab,
            "switch_tab": self.switch_tab,
            "scroll": self.scroll,
            "upload_file": self.upload_file,
            "batch": self.batch,
        }

        if action not in actions:
            raise ValueError(f"Unknown browser action: {action}")

        return actions[action](**arguments)

    def batch(self, actions: list[dict[str, Any]]) -> list[Any]:
        """Run simple actions that do not change the page."""

        allowed = {
            "type",
            "select_option",
            "check",
            "uncheck",
            "press_key",
        }
        results = []

        for item in actions:
            action = item["action"]

            if action not in allowed:
                raise ValueError(f"Action cannot be batched: {action}")

            results.append(
                self.execute(action, item.get("arguments", {}))
            )

        return results

    def navigate(self, url: str) -> str:
        """Open a URL in the current tab."""

        page = self.get_page()
        page.goto(url)

        return page.url

    def click(self, ref: str) -> str:
        """Click the browser element from the latest observation."""

        self.get_element(ref).click()

        return f"Clicked {ref}"

    def type_text(
        self,
        ref: str,
        text: str,
        press_enter: bool = False,
    ) -> str:
        """Put text into a browser element from the latest observation."""

        element = self.get_element(ref)
        element.fill(text)

        if press_enter:
            element.press("Enter")

        return f"Entered text into {ref}"

    def press_key(self, key: str) -> str:
        """Press a keyboard key on the current page."""

        self.get_page().keyboard.press(key)

        return f"Pressed {key}"

    def select_option(
        self,
        ref: str,
        option: str,
    ) -> str:
        """Choose an option from a browser element."""

        self.get_element(ref).select_option(label=option)

        return f'Selected "{option}" from {ref}'

    def check(self, ref: str) -> str:
        """Check a checkbox or radio control."""

        self.get_element(ref).check()

        return f"Checked {ref}"

    def uncheck(self, ref: str) -> str:
        """Uncheck a checkbox."""

        self.get_element(ref).uncheck()

        return f"Unchecked {ref}"

    def go_back(self) -> str:
        """Go back one page in browser history."""

        page = self.get_page()
        page.go_back()

        return page.url

    def new_tab(self, url: str = "about:blank") -> str:
        """Open a new tab and make it active."""

        page = self.get_page().context.new_page()
        self.set_page(page)

        if url != "about:blank":
            page.goto(url)

        return page.url

    def close_tab(self) -> str:
        """Close the active tab and switch to another one."""

        page = self.get_page()
        pages = page.context.pages

        if len(pages) <= 1:
            raise RuntimeError("Cannot close the only open tab.")

        page.close()

        next_page = page.context.pages[-1]
        self.set_page(next_page)
        next_page.bring_to_front()

        return next_page.url

    def switch_tab(self, index: int) -> str:
        """Switch to an open tab by its zero-based index."""

        pages = self.get_page().context.pages

        if index < 0 or index >= len(pages):
            raise ValueError(f"Tab {index} does not exist.")

        page = pages[index]
        self.set_page(page)
        page.bring_to_front()

        return page.url

    def scroll(self, amount: int = 600) -> str:
        """Scroll the current page up or down."""

        self.get_page().mouse.wheel(0, amount)

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
