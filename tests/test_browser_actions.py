"""Unit tests for browser action safety."""

import unittest

from browser_actions import BrowserActions


class FakeElement:
    def __init__(self):
        self.clicked = False
        self.value = ""
        self.checked = False

    def click(self):
        self.clicked = True

    def fill(self, text):
        self.value = text

    def press(self, key):
        self.last_key = key

    def check(self):
        self.checked = True


class FakePage:
    pass


class BrowserActionsTests(unittest.TestCase):
    def test_click_uses_element_ref(self):
        """Chexsa should execute the exact element ref it observed."""

        elements = {"e2": FakeElement()}
        actions = BrowserActions(
            get_page=lambda: FakePage(),
            set_page=lambda page: None,
            get_element=lambda ref: elements[ref],
        )

        result = actions.click("e2")

        self.assertTrue(elements["e2"].clicked)
        self.assertEqual(result, "Clicked e2")

    def test_type_uses_element_ref(self):
        """Typing should target the selected browser ref."""

        elements = {"e4": FakeElement()}
        actions = BrowserActions(
            get_page=lambda: FakePage(),
            set_page=lambda page: None,
            get_element=lambda ref: elements[ref],
        )

        actions.type_text("e4", "hello", press_enter=True)

        self.assertEqual(elements["e4"].value, "hello")
        self.assertEqual(elements["e4"].last_key, "Enter")

    def test_safe_batch_runs_in_order(self):
        """Safe browser actions should run in one batch."""

        actions = BrowserActions(
            get_page=lambda: FakePage(),
            set_page=lambda page: None,
            get_element=lambda ref: FakeElement(),
        )
        calls = []

        actions.type_text = lambda **args: calls.append(
            ("type", args)
        ) or "typed"
        actions.check = lambda **args: calls.append(
            ("check", args)
        ) or "checked"

        results = actions.batch(
            [
                {
                    "action": "type",
                    "arguments": {
                        "ref": "e1",
                        "text": "test@example.com",
                    },
                },
                {
                    "action": "check",
                    "arguments": {
                        "ref": "e2",
                    },
                },
            ]
        )

        self.assertEqual(results, ["typed", "checked"])
        self.assertEqual(
            [call[0] for call in calls],
            ["type", "check"],
        )

    def test_unsafe_batch_is_rejected(self):
        """Page-changing actions should not run inside a batch."""

        actions = BrowserActions(
            get_page=lambda: FakePage(),
            set_page=lambda page: None,
            get_element=lambda ref: FakeElement(),
        )

        with self.assertRaisesRegex(
            ValueError,
            "Action cannot be batched: click",
        ):
            actions.batch(
                [
                    {
                        "action": "click",
                        "arguments": {"ref": "e1"},
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
