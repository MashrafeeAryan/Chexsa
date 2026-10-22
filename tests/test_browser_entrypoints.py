import sys
import unittest
from unittest.mock import MagicMock, patch

import cli
import voice
from chexsa_browser.models import TaskResult


class EntrypointTests(unittest.TestCase):
    @patch("app_runtime.LLM")
    @patch("app_runtime.create_browser_agent")
    def test_cli_waits_for_input_before_creating_browser(self, factory, model):
        backend, agent = MagicMock(), MagicMock()
        agent.state = None
        agent.last_result = TaskResult("success", "done", "t")
        factory.return_value = backend, agent
        model.return_value.choose_mode.return_value = "browser"
        inputs = iter(["open example", "exit"])
        def read(prompt):
            if not model.called:
                factory.assert_not_called()
            return next(inputs)
        with patch("builtins.input", side_effect=read), patch("builtins.print"):
            cli.main([])
        agent.run.assert_called_once_with("open example")
        backend.close.assert_called_once()

    @patch("app_runtime.LLM")
    @patch("app_runtime.create_browser_agent")
    @patch("builtins.input", return_value="exit")
    def test_cli_exit_needs_no_api_or_browser(self, user_input, factory, model):
        with patch("builtins.print"):
            cli.main([])
        model.assert_not_called()
        factory.assert_not_called()

    @patch("cli.TaskJournal")
    @patch("app_runtime.LLM")
    def test_listing_tasks_needs_no_model_or_browser(self, model, journal):
        journal.return_value.recent.return_value = []
        cli.main(["--tasks"])
        model.assert_not_called()
        journal.return_value.close.assert_called_once()

    @patch("app_runtime.LLM")
    @patch("app_runtime.create_browser_agent")
    def test_resume_uses_saved_task_id_without_classifying_it(self, factory, model):
        backend, agent = MagicMock(), MagicMock()
        factory.return_value = backend, agent
        agent.run_task.return_value = TaskResult("uncertain", "Needs inspection", "saved")
        with patch("builtins.print"):
            cli.main(["--resume", "saved"])
        agent.run_task.assert_called_once_with(task_id="saved")
        model.return_value.choose_mode.assert_not_called()
        backend.close.assert_called_once()

    @patch("app_runtime.LLM")
    @patch("app_runtime.create_browser_agent")
    @patch("voice.listen_text", side_effect=["hello nearby", "Hey Chexsa stop listening"])
    def test_voice_waiting_for_wake_phrase_does_not_open_chrome(self, listen, factory, model):
        speech = MagicMock()
        with patch.dict(sys.modules, {"speech_recognition": speech}), patch("builtins.print"):
            voice.main()
        factory.assert_not_called()
        model.assert_not_called()
