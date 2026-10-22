"""Wake phrases are recognized before any task or browser starts."""

import unittest

from voice import extract_command


class VoiceTests(unittest.TestCase):
    def test_extracts_command_after_wake_phrase(self):
        self.assertEqual(extract_command("Hey Chexsa, search JavaScript tutorials on YouTube"), "search JavaScript tutorials on YouTube")

    def test_wake_phrase_is_case_insensitive(self):
        self.assertEqual(extract_command("HEY CHEXSA open GitHub"), "open GitHub")

    def test_ignores_speech_without_wake_phrase(self):
        self.assertIsNone(extract_command("search JavaScript tutorials"))

    def test_wake_phrase_can_be_spoken_alone(self):
        self.assertEqual(extract_command("Hey Chexsa"), "")
