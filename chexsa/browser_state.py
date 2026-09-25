"""Read the current browser state for Chexsa."""


class BrowserState:
    """Get the current URL, ARIA state, and DOM from a Playwright page."""

    def __init__(self, page):
        self.page = page

    def get_state(self) -> dict:
        """Return the current browser state."""
        return {
            "url": self.page.url,
            "aria": self._get_aria(),
            "dom": self._get_dom(),
        }

    def _get_aria(self):
        """Get the page accessibility snapshot."""
        return self.page.accessibility.snapshot()

    def _get_dom(self):
        """Get the current page HTML."""
        return self.page.content()
