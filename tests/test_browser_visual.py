import unittest
import hashlib
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

    def test_validation_waits_for_render_but_rejects_changed_images(self):
        viewport = {"width": 900, "height": 700, "version": 2}
        session = SimpleNamespace(page_id="tab", epochs={})
        visual = VisualTargeting(SimpleNamespace(session=session, observation=SimpleNamespace(id="o1")))
        visual._viewport = lambda: viewport
        visual.ticket = {"id": "image", "observation": "o1", "page": "tab", "epochs": {}, "viewport": viewport, "digest": hashlib.sha256(b"original").hexdigest()}
        visual._settled_image = Mock(return_value=(b"original", {**viewport, "version": 6}))
        self.assertEqual(visual._check("image"), visual.ticket)
        visual._settled_image = Mock(return_value=(b"changed canvas", {**viewport, "version": 6}))
        with self.assertRaises(BrowserError):
            visual._check("image")

    def test_validation_rejects_viewport_changes_during_capture(self):
        viewport = {"width": 900, "height": 700, "version": 2}
        session = SimpleNamespace(page_id="tab", epochs={})
        visual = VisualTargeting(SimpleNamespace(session=session, observation=SimpleNamespace(id="o1")))
        visual._viewport = lambda: viewport
        visual.ticket = {"id": "image", "observation": "o1", "page": "tab", "epochs": {}, "viewport": viewport, "digest": hashlib.sha256(b"original").hexdigest()}
        visual._settled_image = Mock(return_value=(b"original", {**viewport, "width": 901}))
        with self.assertRaises(BrowserError):
            visual._check("image")

    def test_validation_rejects_navigation_during_capture(self):
        viewport = {"width": 900, "height": 700, "version": 2}
        session = SimpleNamespace(page_id="tab", epochs={"tab": 0})
        visual = VisualTargeting(SimpleNamespace(session=session, observation=SimpleNamespace(id="o1")))
        visual._viewport = lambda: viewport
        visual.ticket = {"id": "image", "observation": "o1", "page": "tab", "epochs": {"tab": 0}, "viewport": viewport, "digest": hashlib.sha256(b"original").hexdigest()}
        def navigate():
            session.epochs["tab"] += 1
            return b"original", viewport
        visual._settled_image = navigate
        with self.assertRaises(BrowserError):
            visual._check("image")
