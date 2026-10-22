"""Real Chrome tests. Run explicitly; no accounts, model keys, or real email used."""

import functools
import http.server
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chexsa_browser.backend import BrowserBackend
from chexsa_browser.models import ActionRequest
from chexsa_browser.session import BrowserSession


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class BrowserIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(QuietHandler, directory=str(Path(__file__).parent / "fixtures"))
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        cls.session = BrowserSession()
        cls.session.connect()

    @classmethod
    def tearDownClass(cls):
        cls.session.close()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        self.page = self.session.get_page().context.new_page()
        self.session.select(self.page)
        self.backend = BrowserBackend(self.session, context_budget=4000)
        self.page.goto(self.base + "/controls.html")
        self.backend.observe()

    def tearDown(self):
        if not self.page.is_closed():
            self.page.close()
        pages = self.session.pages()
        if pages:
            self.session.select(pages[-1])

    def element(self, name, role=None):
        matches = [e for e in self.backend.observation.elements if e.name == name and (role is None or e.role == role)]
        self.assertEqual(len(matches), 1, (name, [(e.role, e.name) for e in matches]))
        return matches[0]

    def act(self, action, **arguments):
        result = self.backend.execute(ActionRequest(action, arguments))
        self.assertEqual(result.status, "ok", result)
        return result

    def test_duplicate_refs_survive_reordering_without_guessing(self):
        buttons = [e for e in self.backend.observation.elements if e.role == "button" and e.name == "Send"]
        self.assertEqual(len(buttons), 2)
        first, second = buttons
        self.page.evaluate("document.querySelector('#first').before(document.querySelector('#second'))")
        self.act("click", ref=second.ref)
        self.assertEqual(self.page.locator("#second").get_attribute("data-clicked"), "yes")
        self.assertIsNone(self.page.locator("#first").get_attribute("data-clicked"))
        self.act("click", ref=first.ref)
        self.assertEqual(self.page.locator("#first").get_attribute("data-clicked"), "yes")

    def test_stale_replaced_and_unknown_targets(self):
        old = self.element("Name").ref
        self.backend.observe()
        self.assertEqual(self.backend.execute(ActionRequest("type", {"ref": old, "text": "wrong"})).code, "stale_target")
        current = self.element("Name").ref
        self.page.evaluate("document.querySelector('input[aria-label=Name]').outerHTML='<input aria-label=Name>'")
        self.assertEqual(self.backend.execute(ActionRequest("type", {"ref": current, "text": "wrong"})).code, "target_detached")
        self.assertEqual(self.page.get_by_role("textbox", name="Name", exact=True).input_value(), "")
        self.assertEqual(self.backend.execute(ActionRequest("click", {"ref": "invented"})).code, "stale_target")

    def test_form_actions_shadow_dom_frame_and_upload(self):
        self.act("type", ref=self.element("Name").ref, text="Literal {text} + unicode café")
        self.act("select_option", ref=self.element("Colour", "combobox").ref, option="Red")
        self.act("check", ref=self.element("Choice").ref)
        self.act("uncheck", ref=self.element("Choice").ref)
        self.act("click", ref=self.element("Shadow action").ref)
        self.act("type", ref=self.element("Frame value").ref, text="Inside frame")
        self.act("click", ref=self.element("Frame action").ref)
        self.assertEqual(self.page.frame_locator("iframe").get_by_role("textbox").input_value(), "Inside frame")
        self.assertEqual(self.page.frame_locator("iframe").get_by_role("button").get_attribute("data-clicked"), "yes")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_text("fixture attachment", encoding="utf-8")
            self.act("upload_file", ref=self.element("Upload").ref, file_path=str(path))
        self.assertEqual(self.page.get_by_label("Name", exact=True).input_value(), "Literal {text} + unicode café")
        self.assertFalse(self.page.get_by_label("Choice").is_checked())
        self.assertEqual(self.page.get_by_label("Colour").input_value(), "Red")

    def test_large_page_search_regions_and_autocomplete(self):
        self.page.goto(self.base + "/mail.html?rows=350")
        observation = self.backend.observe()
        self.assertGreater(len(observation.elements), 700)
        self.assertLessEqual(len(observation.context), 4000)
        self.assertEqual(self.act("find_elements", query="Open message 349").data["elements"][0]["name"], "Open message 349")
        self.act("click", ref=self.element("Compose").ref)
        observation = self.backend.observe()
        self.assertIn("Recipients", observation.context)
        self.assertNotIn("Open message 349", observation.context)
        self.act("type", ref=self.element("Recipients").ref, text="fixture@example.test", press_enter=True)
        self.backend.observe()
        self.assertIn("fixture@example.test", self.backend.observation.context)

    def test_navigation_tabs_scroll_and_batch(self):
        self.act("batch", actions=[{"action": "type", "arguments": {"ref": self.element("Name").ref, "text": "batch"}}, {"action": "check", "arguments": {"ref": self.element("Choice").ref}}])
        self.act("scroll", amount=500)
        self.page.wait_for_timeout(100)
        self.assertGreater(self.page.evaluate("scrollY"), 0)
        old_ref = self.element("Name").ref
        self.act("navigate", url=self.base + "/frame.html")
        self.assertEqual(self.backend.execute(ActionRequest("type", {"ref": old_ref, "text": "wrong"})).code, "stale_target")
        self.act("go_back")
        old_page_id = self.session.page_id
        self.backend.observe()
        self.act("new_tab", url=self.base + "/frame.html")
        opened = self.session.get_page()
        try:
            self.backend.observe()
            self.act("switch_tab", page_id=old_page_id)
            self.backend.observe()
            self.act("switch_tab", page_id=self.session.page_identifier(opened))
            self.act("close_tab")
        finally:
            if not opened.is_closed():
                opened.close()
            self.session.select(self.page)

    def test_unsafe_batch_has_no_partial_side_effects(self):
        request = ActionRequest("batch", {"actions": [{"action": "type", "arguments": {"ref": self.element("Name").ref, "text": "should not run"}}, {"action": "click", "arguments": {"ref": "invented"}}]})
        self.assertEqual(self.backend.execute(request).code, "unsafe_batch")
        self.assertEqual(self.page.get_by_label("Name", exact=True).input_value(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
