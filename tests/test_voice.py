"""Unit tests for Chexsa's wake phrase."""

import unittest

from voice import extract_command, is_word_write_command, run_command


class FakeBrowserAgent:
    def __init__(self):
        self.requests = []

    def run(self, command):
        self.requests.append(command)
        return "Browser task done."


class FakeLLM:
    def __init__(self):
        self.requests = []

    def generate_text(self, command):
        self.requests.append(command)
        return "Generated essay."


class FakeDesktop:
    def __init__(self):
        self.written_text = []

    def write_word(self, text):
        self.written_text.append(text)
        return "Wrote text in Word."


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


    def test_detects_word_writing_command(self):
        """Word writing requests should use desktop automation."""

        self.assertTrue(
            is_word_write_command("Write me an essay in Word")
        )

    def test_normal_command_stays_in_browser(self):
        """Normal web requests should stay on the browser path."""

        self.assertFalse(
            is_word_write_command("Search JavaScript tutorials on YouTube")
        )

    def test_word_command_generates_and_writes_text(self):
        """A Word request should generate text and send it to Word."""

        browser = FakeBrowserAgent()
        llm = FakeLLM()
        desktop = FakeDesktop()

        response = run_command(
            "Write me an essay in Word",
            browser,
            llm,
            desktop,
        )

        self.assertEqual(response, "I wrote it in Word.")
        self.assertEqual(
            llm.requests,
            ["Write me an essay in Word"],
        )
        self.assertEqual(
            desktop.written_text,
            ["Generated essay."],
        )
        self.assertEqual(browser.requests, [])

    def test_browser_command_uses_existing_agent(self):
        """A non-Word request should use the browser agent."""

        browser = FakeBrowserAgent()
        llm = FakeLLM()
        desktop = FakeDesktop()

        response = run_command(
            "Search JavaScript tutorials on YouTube",
            browser,
            llm,
            desktop,
        )

        self.assertEqual(response, "Browser task done.")
        self.assertEqual(
            browser.requests,
            ["Search JavaScript tutorials on YouTube"],
        )
        self.assertEqual(llm.requests, [])
        self.assertEqual(desktop.written_text, [])


if __name__ == "__main__":
    unittest.main()
