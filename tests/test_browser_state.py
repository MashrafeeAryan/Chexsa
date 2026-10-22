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


    def test_initial_state_has_no_diff(self):
        """The first observation should establish the baseline."""

        state = BrowserState()

        changes = state._get_changes(
            '- button "Compose"',
            "Inbox",
        )

        self.assertEqual(changes, "Initial page state.")

    def test_changes_show_added_and_removed_content(self):
        """Later observations should report what changed."""

        state = BrowserState()
        state.previous_aria = '- button "Compose"\n- link "Inbox"'
        state.previous_text = "Inbox\nOld message"

        changes = state._get_changes(
            '- button "Compose"\n- textbox "To"',
            "Inbox\nMessage sent",
        )

        self.assertIn('Added controls:\n- textbox "To"', changes)
        self.assertIn('Removed controls:\n- link "Inbox"', changes)
        self.assertIn("Added text:\nMessage sent", changes)
        self.assertIn("Removed text:\nOld message", changes)

    def test_changes_are_limited_for_large_pages(self):
        """Large page changes should stay small for the model."""

        state = BrowserState(max_changes_chars=80)
        state.previous_aria = ""
        state.previous_text = ""

        changes = state._get_changes(
            "\n".join(
                f'- button "Button {index}"'
                for index in range(100)
            ),
            "\n".join(
                f"Message {index}"
                for index in range(100)
            ),
        )

        self.assertLessEqual(len(changes), 80)


    def test_late_new_text_is_not_lost_on_large_page(self):
        """A new result at the end of a large page should still appear."""

        state = BrowserState(max_changes_chars=200)
        old_text = "\n".join(
            f"Existing message {index}"
            for index in range(500)
        )
        state.previous_aria = ""
        state.previous_text = old_text

        changes = state._get_changes(
            "",
            old_text + "\nMessage sent",
        )

        self.assertIn("Message sent", changes)


if __name__ == "__main__":
    unittest.main()
