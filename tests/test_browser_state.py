"""Unit tests for Chexsa's compact browser state."""

import unittest

from browser_state import BrowserState


class FakeLocator:
    def aria_snapshot(self):
        return """- button "Compose"
- paragraph: Inbox text
- textbox "Search mail"
- link "Inbox"
- button "Refresh"
"""

    def inner_text(self):
        return "abcdefghijklmnopqrstuvwxyz"


class FakePage:
    def locator(self, selector):
        return FakeLocator()


class BrowserStateTests(unittest.TestCase):
    def test_aria_keeps_useful_roles(self):
        """ARIA filtering should keep controls and remove plain text."""

        state = BrowserState(max_aria_chars=1000)
        aria = state._get_aria(FakePage())

        self.assertIn('button "Compose"', aria)
        self.assertIn('textbox "Search mail"', aria)
        self.assertNotIn("paragraph", aria)

    def test_aria_respects_character_limit(self):
        """Large ARIA output should be capped."""

        state = BrowserState(max_aria_chars=20)
        aria = state._get_aria(FakePage())

        self.assertLessEqual(len(aria), 20)

    def test_visible_text_respects_character_limit(self):
        """Visible page text should be capped."""

        state = BrowserState(max_text_chars=10)
        text = state._get_visible_text(FakePage())

        self.assertEqual(text, "abcdefghij")


if __name__ == "__main__":
    unittest.main()
