import unittest
from types import SimpleNamespace

from chexsa_browser.actions import validate
from chexsa_browser.models import ActionRequest, BrowserError
from chexsa_browser.visual import VisualTargeting


class VisualTests(unittest.TestCase):
    def test_coordinate_arguments_reject_boolean_values(self):
        with self.assertRaises(BrowserError):
            validate(ActionRequest("click_coordinates", {"x": True, "y": 20, "screenshot_id": "image"}))
        validate(ActionRequest("click_coordinates", {"x": 10.5, "y": 20, "screenshot_id": "image"}))

    def test_no_screenshot_means_no_coordinate_click(self):
        visual = VisualTargeting(SimpleNamespace(session=SimpleNamespace()))
        with self.assertRaises(BrowserError):
            visual.click(10, 20, "invented")
