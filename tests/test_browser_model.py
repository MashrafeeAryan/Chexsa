import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

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

    def test_provider_adapters_preserve_json_images_and_usage(self):
        for provider in ("gemini", "openai_compatible"):
            with self.subTest(provider=provider):
                client = MagicMock()
                model = BrowserModel(SimpleNamespace(provider=provider, model="configured-model", client=client))
                if provider == "gemini":
                    client.models.generate_content.return_value = SimpleNamespace(text='{"result":"ok"}', usage_metadata=SimpleNamespace(prompt_token_count=12, candidates_token_count=3))
                else:
                    client.chat.completions.create.return_value = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"result":"ok"}'))], usage=SimpleNamespace(prompt_tokens=12, completion_tokens=3))
                self.assertEqual(model._ask("Return JSON", b"image bytes"), {"result": "ok"})
                self.assertEqual(model.usage, {"calls": 1, "input_tokens": 12, "output_tokens": 3})
