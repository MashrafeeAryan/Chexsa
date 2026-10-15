"""Unit tests for Chexsa's wake phrase."""

import unittest

from voice import extract_command


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


if __name__ == "__main__":
    unittest.main()
