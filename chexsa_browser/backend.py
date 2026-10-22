"""Browser backend: a complete local observation and a compact model-facing view."""

import hashlib
from dataclasses import asdict

from .collector import Collector
from .models import BrowserError, Observation
from .session import BrowserSession
from .targets import TargetRegistry


class BrowserBackend:
    def __init__(self, session=None, **session_options):
        self.session = session or BrowserSession(**session_options)
        self.registry = TargetRegistry(self.session)
        self.collector = Collector(self.session)
        self.observation = None
        self.sequence = 0

    def connect(self):
        self.session.connect()

    def observe(self):
        self.registry.invalidate()
        page = self.session.get_page()
        before = dict(self.session.epochs)
        elements, text, issues = self.collector.collect()
        tabs = self.session.tabs()
        if any(self.session.epochs.get(key) != value for key, value in before.items()):
            raise BrowserError("stale_observation", "The page navigated during observation. Observe again.")
        self.registry.bind(elements)
        self.sequence += 1
        fingerprint = hashlib.sha256(repr((page.url, [(e.identity, e.signature()) for e in elements], text)).encode()).hexdigest()
        result = Observation(f"o{self.sequence}", self.session.page_id, page.url, page.title(), tabs, elements, text, issues, fingerprint=fingerprint)
        self.observation = result
        return result

    def close(self):
        self.registry.invalidate()
        self.session.close()
