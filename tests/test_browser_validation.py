import unittest

from chexsa_browser.actions import validate
from chexsa_browser.models import ActionRequest, BrowserError


class ValidationTests(unittest.TestCase):
    def test_rejects_missing_extra_and_wrong_arguments(self):
        for request in (ActionRequest("click"), ActionRequest("click", {"ref": "e1", "selector": "button"}), ActionRequest("switch_tab", {"index": True}), ActionRequest("unknown")):
            with self.subTest(request=request), self.assertRaises(BrowserError):
                validate(request)

    def test_entire_batch_is_validated_before_execution(self):
        for action in ("click", "navigate", "scroll", "upload_file", "batch", "press_key"):
            arguments = {"key": "Enter"} if action == "press_key" else {}
            request = ActionRequest("batch", {"actions": [{"action": "type", "arguments": {"ref": "e1", "text": "hello"}}, {"action": action, "arguments": arguments}]})
            with self.subTest(action=action), self.assertRaises(BrowserError):
                validate(request)

    def test_safe_batch_and_ref_actions_are_valid(self):
        validate(ActionRequest("batch", {"actions": [{"action": "type", "arguments": {"ref": "e1", "text": "hello"}}, {"action": "check", "arguments": {"ref": "e2"}}]}))
