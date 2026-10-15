"""Unit tests for browser action safety."""

import unittest

from browser_actions import BrowserActions


class FakeLocator:
    def __init__(self, count):
        self._count = count

    def count(self):
        return self._count


class FakePage:
    def __init__(self, count=1):
        self.count = count

    def get_by_role(self, role, name):
        return FakeLocator(self.count)


class BrowserActionsTests(unittest.TestCase):
    def test_ambiguous_target_is_rejected(self):
        """Chexsa should not guess when multiple controls match."""

        actions = BrowserActions(
            get_page=lambda: FakePage(count=2),
            set_page=lambda page: None,
        )

        with self.assertRaisesRegex(
            RuntimeError,
            'Expected one button "Send", found 2.',
        ):
            actions._get_element("button", "Send")

    def test_safe_batch_runs_in_order(self):
        """Safe browser actions should run in one batch."""

        actions = BrowserActions(
            get_page=lambda: FakePage(),
            set_page=lambda page: None,
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
                        "role": "textbox",
                        "name": "Email",
                        "text": "test@example.com",
                    },
                },
                {
                    "action": "check",
                    "arguments": {
                        "role": "checkbox",
                        "name": "Remember me",
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
        )

        with self.assertRaisesRegex(
            ValueError,
            "Action cannot be batched: click",
        ):
            actions.batch(
                [
                    {
                        "action": "click",
                        "arguments": {
                            "role": "button",
                            "name": "Send",
                        },
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
