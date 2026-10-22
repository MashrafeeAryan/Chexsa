"""Keep browser scenarios local and independent of accounts or model APIs."""

import unittest
from pathlib import Path


class BrowserFixtureTests(unittest.TestCase):
    def test_mail_exposes_success_failure_and_uncertainty(self):
        fixture = (Path(__file__).parent / "fixtures" / "mail.html").read_text()
        for text in ("sendCount", "Message sent", "mode==='failure'", "mode!=='uncertain'", "Committed recipients"):
            self.assertIn(text, fixture)

    def test_controls_include_duplicate_and_nonstandard_targets(self):
        fixture = (Path(__file__).parent / "fixtures" / "controls.html").read_text()
        self.assertEqual(fixture.count('>Send</button>'), 2)
        self.assertIn('attachShadow', fixture)
        self.assertIn('<iframe', fixture)
        self.assertIn('<canvas', fixture)
