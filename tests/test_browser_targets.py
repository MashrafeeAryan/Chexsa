import unittest
from types import SimpleNamespace

from chexsa_browser.models import BrowserError, Element
from chexsa_browser.targets import TargetRegistry


class Client:
    def __init__(self):
        self.calls = []
        self.connected = True

    def send(self, method, args):
        self.calls.append((method, args))
        if method == "DOM.resolveNode":
            return {"object": {"objectId": str(args["backendNodeId"])}}
        return {"result": {"value": {"connected": self.connected, "disabled": False, "readonly": False}}}


class TargetTests(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        self.session = SimpleNamespace(page_id="page", clients={"target": self.client}, epochs={"target": 0})
        self.registry = TargetRegistry(self.session)

    def element(self, node):
        return Element("target", "frame", "doc", node, "button", "Send", capabilities=("click",))

    def test_duplicate_controls_resolve_the_recorded_node(self):
        first, second = self.element(11), self.element(22)
        self.registry.bind([first, second])
        self.assertEqual(self.registry.resolve(second.ref, "click").object_id, "22")
        self.assertEqual(self.registry.resolve(first.ref, "click").object_id, "11")

    def test_refresh_and_empty_observation_reject_old_refs(self):
        first = self.element(11)
        self.registry.bind([first])
        old = first.ref
        self.registry.bind([self.element(22)])
        self.assertNotIn(old, self.registry.refs)
        with self.assertRaises(BrowserError):
            self.registry.resolve(old)
        self.registry.bind([])
        self.assertFalse(self.registry.refs)

    def test_navigation_page_changes_and_detachment_are_rejected(self):
        for change in ("page", "epoch", "detached"):
            with self.subTest(change=change):
                self.setUp()
                element = self.element(11)
                self.registry.bind([element])
                if change == "page":
                    self.session.page_id = "other"
                elif change == "epoch":
                    self.session.epochs["target"] += 1
                else:
                    self.client.connected = False
                with self.assertRaises(BrowserError):
                    self.registry.resolve(element.ref)

    def test_capability_is_checked_before_browser_execution(self):
        element = self.element(11)
        self.registry.bind([element])
        with self.assertRaisesRegex(BrowserError, "does not support type"):
            self.registry.resolve(element.ref, "type")
        self.assertFalse(self.client.calls)

    def test_same_node_renamed_to_another_action_is_stale(self):
        element = self.element(11)
        element.states.update(_ax_role="button", _ax_name="Send")
        original = self.client.send
        def send(method, arguments):
            if method == "Accessibility.getPartialAXTree":
                return {"nodes": [{"backendDOMNodeId": 11, "role": {"value": "button"}, "name": {"value": "Delete"}}]}
            return original(method, arguments)
        self.client.send = send
        self.registry.bind([element])
        with self.assertRaisesRegex(BrowserError, "accessible name changed"):
            self.registry.resolve(element.ref, "click")
