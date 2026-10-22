import unittest
from types import SimpleNamespace

from chexsa_browser.agent import BrowserAgent
from chexsa_browser.models import ActionRequest, ActionResult, Observation, TaskSpec, TaskState
from chexsa_browser.verification import completion_is_supported


class FakeBackend:
    def __init__(self):
        self.calls = []
        self.observation = Observation("o1", "p", "url", "title", [], [], {"status": {"text": "Ready", "region_path": ()}}, context="Ready", fingerprint="same")

    def observe(self):
        return self.observation

    def execute(self, action):
        self.calls.append(action)
        return ActionResult(action.action, "ok", executed=True)

    def wait_for_change(self, *args):
        pass


class FakeModel:
    def plan(self, request, observation, state=None):
        return TaskSpec(request, subgoals=["work"], completion=["done"])

    def choose(self, state, observation):
        return ActionRequest("finish", {"response": "Done"})

    def verify(self, *args):
        return {"complete": True, "evidence": ["invented"], "progress": "", "reason": ""}


class BrowserAgentTests(unittest.TestCase):
    def test_completion_requires_real_evidence(self):
        backend = FakeBackend()
        agent = BrowserAgent(backend, FakeModel(), emit=lambda text: None)
        result = agent.run_task("task")
        self.assertEqual(result.status, "blocked")
        self.assertFalse(backend.calls)

    def test_repeated_actions_replan_then_stop(self):
        backend, model = FakeBackend(), FakeModel()
        model.choose = lambda *args: ActionRequest("scroll", {"amount": 0})
        result = BrowserAgent(backend, model, emit=lambda text: None).run_task("task")
        self.assertEqual(result.status, "blocked")
        self.assertLess(len(backend.calls), 10)

    def test_question_preserves_task_and_original_values(self):
        model = FakeModel()
        model.choose = lambda *args: ActionRequest("ask_user", {"question": "Which account?"})
        agent = BrowserAgent(FakeBackend(), model, emit=lambda text: None)
        result = agent.run_task("send to intended@example.test")
        self.assertEqual(result.status, "blocked")
        self.assertIn("intended@example.test", agent.state.spec.goal)
        self.assertEqual(agent.state.question, "Which account?")

    def test_old_confirmation_cannot_prove_a_new_send(self):
        state = TaskState("t", TaskSpec("send", inputs={"recipient": "x@example.test"}))
        state.submission, state.email_checked = "uncertain", True
        state.commit_baseline = "Message sent"
        observation = Observation("o1", "p", "url", "title", [], [], {"x": {"text": "Message sent", "region_path": ()}})
        self.assertFalse(completion_is_supported(state, observation, {"complete": True, "evidence": ["Message sent"]}))

    def test_draft_task_blocks_submission(self):
        backend, model = FakeBackend(), FakeModel()
        model.plan = lambda *args: TaskSpec("draft", intent="draft")
        model.choose = lambda *args: ActionRequest("click", {"ref": "e1"}, {"kind": "submission"})
        result = BrowserAgent(backend, model, emit=lambda text: None).run_task("draft")
        self.assertEqual(result.status, "blocked")
        self.assertFalse(backend.calls)
