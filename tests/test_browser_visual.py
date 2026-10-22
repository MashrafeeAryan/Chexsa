import unittest
from types import SimpleNamespace
from unittest.mock import Mock

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

    def test_capture_waits_for_matching_rendered_frames(self):
        page = SimpleNamespace(screenshot=Mock(side_effect=[b"initial paint", b"settled", b"settled"]))
        visual = VisualTargeting(SimpleNamespace(session=SimpleNamespace(get_page=lambda: page)))
        viewport = {"width": 900, "height": 700, "dpr": 2}
        visual._viewport = lambda: viewport
        self.assertEqual(visual._settled_image(), (b"settled", viewport))
        self.assertEqual(page.screenshot.call_count, 3)

    def test_capture_records_post_screenshot_mutation_version(self):
        page = SimpleNamespace(screenshot=Mock(return_value=b"settled"))
        visual = VisualTargeting(SimpleNamespace(session=SimpleNamespace(get_page=lambda: page)))
        visual._viewport = Mock(side_effect=[{"width": 900, "version": 2}, {"width": 900, "version": 4}])
        self.assertEqual(visual._settled_image(), (b"settled", {"width": 900, "version": 4}))
        self.assertEqual(page.screenshot.call_count, 2)

    def test_dynamic_page_capture_has_a_bounded_cost(self):
        page = SimpleNamespace(screenshot=Mock(side_effect=[b"1", b"2", b"3", b"4"]))
        visual = VisualTargeting(SimpleNamespace(session=SimpleNamespace(get_page=lambda: page)))
        viewport = {"width": 900, "height": 700, "dpr": 2}
        visual._viewport = lambda: viewport
        self.assertEqual(visual._settled_image(), (b"4", viewport))
        self.assertEqual(page.screenshot.call_count, 4)
