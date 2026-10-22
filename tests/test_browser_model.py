import unittest

from chexsa_browser.model import BrowserModel, parse_object
from chexsa_browser.models import BrowserError, Observation, TaskSpec, TaskState


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.model = BrowserModel(None)
        self.observation = Observation("o1", "p", "url", "title", [], [], {}, context="page")

    def test_plan_preserves_the_users_literal_address(self):
        self.model._ask = lambda *args: {"inputs": {"recipient": "hallucinated@example.test"}, "subgoals": ["compose"], "completion": ["sent"], "intent": "act"}
        spec = self.model.plan("send hello to intended@example.test", self.observation)
        self.assertEqual(spec.inputs["recipient"], "intended@example.test")

    def test_invalid_action_and_malformed_plan_are_rejected(self):
        self.model._ask = lambda *args: {"action": "click", "arguments": {"selector": "button"}}
        with self.assertRaises(BrowserError):
            self.model.choose(TaskState("t", TaskSpec("goal")), self.observation)
        self.model._ask = lambda *args: {"subgoals": "not a list"}
        with self.assertRaises(BrowserError):
            self.model.plan("goal", self.observation)

    def test_non_object_json_is_rejected(self):
        for text in ('[]', 'null', '```json {} ```'):
            with self.assertRaises(BrowserError):
                parse_object(text)

    def test_incomplete_email_plan_cannot_bypass_preflight(self):
        self.model._ask = lambda *args: {"inputs": {}, "subgoals": ["compose"], "completion": ["draft exists"], "intent": "act"}
        spec = self.model.plan("draft an email to intended@example.test", self.observation)
        self.assertEqual(spec.intent, "draft")
        self.assertEqual(spec.inputs["recipient"], "intended@example.test")
        self.assertIn("body", spec.inputs)
