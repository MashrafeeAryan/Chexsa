import tempfile
import unittest
from pathlib import Path

from chexsa_browser.agent import BrowserAgent
from chexsa_browser.journal import TaskJournal
from chexsa_browser.models import ActionRequest, TaskSpec, TaskState
from test_browser_agent import FakeBackend, FakeModel


class JournalTests(unittest.TestCase):
    def test_submission_intent_survives_reopening_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.db"
            journal = TaskJournal(path)
            state = TaskState("t", TaskSpec("send", inputs={"recipient": "fixture@example.test"}), submission="attempting")
            journal.save(state)
            journal.close()
            journal = TaskJournal(path)
            restored = journal.load("t")
            self.assertEqual(restored.submission, "attempting")
            self.assertEqual(restored.spec.inputs, state.spec.inputs)
            self.assertEqual(journal.recent()[0]["id"], "t")
            journal.close()

    def test_resume_reconciles_uncertain_submission_without_replaying(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = TaskJournal(Path(directory) / "tasks.db")
            journal.save(TaskState("t", TaskSpec("submit"), submission="attempting"))
            backend, model = FakeBackend(), FakeModel()
            model.choose = lambda *args: ActionRequest("click", {"ref": "old"}, {"kind": "submission"})
            agent = BrowserAgent(backend, model, journal=journal, emit=lambda text: None)
            result = agent.run_task(task_id="t")
            self.assertEqual(result.status, "uncertain")
            self.assertFalse(backend.calls)
            self.assertEqual(journal.load("t").submission, "uncertain")
            journal.close()

    def test_completed_task_is_not_executed_again(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = TaskJournal(Path(directory) / "tasks.db")
            journal.save(TaskState("t", TaskSpec("done"), status="success", result_message="Already done"))
            backend = FakeBackend()
            result = BrowserAgent(backend, FakeModel(), journal=journal).run_task(task_id="t")
            self.assertEqual(result.message, "Already done")
            self.assertFalse(backend.calls)
            journal.close()
