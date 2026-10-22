import unittest
from unittest.mock import MagicMock, patch

import cli
import voice
from chexsa_browser.models import TaskResult


class EntrypointTests(unittest.TestCase):
    @patch("voice.build_browser_agent")
    def test_voice_uses_shared_factory(self, factory):
        factory.return_value = ("backend", "agent")
        self.assertEqual(voice.create_browser_agent("model"), ("backend", "agent"))
        factory.assert_called_once_with("model")

    @patch("cli.LLM")
    @patch("cli.create_browser_agent")
    @patch("builtins.input", side_effect=["open example", "exit"])
    def test_cli_uses_new_agent_and_closes_connection(self, user_input, factory, model):
        backend, agent = MagicMock(), MagicMock()
        factory.return_value = backend, agent
        agent.last_result = TaskResult("success", "done", "t")
        with patch("builtins.print"):
            cli.main([])
        agent.run.assert_called_once_with("open example")
        backend.close.assert_called_once()

    @patch("cli.TaskJournal")
    @patch("cli.LLM")
    def test_listing_tasks_needs_no_model_or_browser(self, model, journal):
        journal.return_value.recent.return_value = []
        cli.main(["--tasks"])
        model.assert_not_called()
        journal.return_value.close.assert_called_once()

    @patch("cli.LLM")
    @patch("cli.create_browser_agent")
    def test_resume_uses_saved_task_id(self, factory, model):
        backend, agent = MagicMock(), MagicMock()
        factory.return_value = backend, agent
        agent.run_task.return_value = TaskResult("uncertain", "Needs inspection", "saved")
        with patch("builtins.print"):
            cli.main(["--resume", "saved"])
        agent.run_task.assert_called_once_with(task_id="saved")
        backend.close.assert_called_once()
