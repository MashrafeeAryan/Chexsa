"""Unit tests for Chexsa's wake phrase."""

import unittest

from voice import extract_command, run_command


class FakeAgent:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def run(self, command):
        self.requests.append(command)
        return self.response


class FakeLLM:
    def __init__(self, mode):
        self.mode = mode
        self.requests = []

    def choose_mode(self, command):
        self.requests.append(command)
        return self.mode


class VoiceTests(unittest.TestCase):
    def test_extracts_command_after_wake_phrase(self):
        """Words after Hey Chexsa should become the browser command."""

        command = extract_command(
            "Hey Chexsa, search JavaScript tutorials on YouTube"
        )

        self.assertEqual(
            command,
            "search JavaScript tutorials on YouTube",
        )

    def test_wake_phrase_is_case_insensitive(self):
        """The wake phrase should work with different capitalization."""

        command = extract_command("HEY CHEXSA open GitHub")

        self.assertEqual(command, "open GitHub")

    def test_ignores_speech_without_wake_phrase(self):
        """Normal nearby speech should not trigger Chexsa."""

        command = extract_command("search JavaScript tutorials")

        self.assertIsNone(command)

    def test_wake_phrase_can_be_spoken_alone(self):
        """A wake phrase by itself should request a second listen."""

        command = extract_command("Hey Chexsa")

        self.assertEqual(command, "")

    def test_desktop_request_uses_desktop_agent(self):
        """Desktop-classified requests should use the desktop agent."""

        browser = FakeAgent("Browser task done.")
        desktop = FakeAgent("Desktop task done.")
        llm = FakeLLM("desktop")

        response = run_command(
            "Write me an essay in Word",
            browser,
            desktop,
            llm,
        )

        self.assertEqual(response, "Desktop task done.")
        self.assertEqual(
            desktop.requests,
            ["Write me an essay in Word"],
        )
        self.assertEqual(browser.requests, [])

    def test_browser_request_uses_browser_agent(self):
        """Browser-classified requests should use the browser agent."""

        browser = FakeAgent("Browser task done.")
        desktop = FakeAgent("Desktop task done.")
        llm = FakeLLM("browser")

        response = run_command(
            "Search JavaScript tutorials on YouTube",
            browser,
            desktop,
            llm,
        )

        self.assertEqual(response, "Browser task done.")
        self.assertEqual(
            browser.requests,
            ["Search JavaScript tutorials on YouTube"],
        )
        self.assertEqual(desktop.requests, [])


if __name__ == "__main__":
    unittest.main()
