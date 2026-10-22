"""Browser backend: a complete local observation and a compact model-facing view."""

import hashlib
import time

from .actions import Executor
from .collector import Collector
from .context import ContextView, changes
from .models import BrowserError, Observation
from .regions import group_regions
from .session import BrowserSession
from .targets import TargetRegistry


class BrowserBackend:
    def __init__(self, session=None, context_budget=12000, **session_options):
        self.session = session or BrowserSession(**session_options)
        self.registry = TargetRegistry(self.session)
        self.collector = Collector(self.session)
        self.observation = None
        self.sequence = 0
        self.view = ContextView(context_budget)
        self.executor = Executor(self)
        self._change_counter = None

    def connect(self):
        self.session.connect()

    def observe(self):
        self.registry.invalidate()
        page = self.session.get_page()
        page.evaluate("""() => {if(!window.__chexsaWatch){window.__chexsaWatch={version:0};const tick=()=>window.__chexsaWatch.version++;new MutationObserver(tick).observe(document,{subtree:true,childList:true,attributes:true,characterData:true});for(const event of ['input','change','scroll'])addEventListener(event,tick,true);} }""")
        before = dict(self.session.epochs)
        elements, text, issues = self.collector.collect()
        tabs = self.session.tabs()
        if any(self.session.epochs.get(key) != value for key, value in before.items()):
            raise BrowserError("stale_observation", "The page navigated during observation. Observe again.")
        self.registry.bind(elements)
        self.sequence += 1
        fingerprint = hashlib.sha256(repr((page.url, [(e.identity, e.signature()) for e in elements], text)).encode()).hexdigest()
        result = Observation(f"o{self.sequence}", self.session.page_id, page.url, page.title(), tabs, elements, text, issues, fingerprint=fingerprint)
        result.regions = group_regions(elements, self.observation)
        result.changes = changes(self.observation, result)
        self.view.render(result)
        self.observation = result
        return result

    def execute(self, request):
        self._change_counter = self.session.get_page().evaluate("window.__chexsaWatch?.version")
        return self.executor.execute(request)

    def wait_for_change(self, timeout=2.0):
        deadline = time.monotonic() + timeout
        changed_at = None
        last = self._change_counter
        while time.monotonic() < deadline:
            page = self.session.get_page()
            try:
                current = page.evaluate("window.__chexsaWatch?.version")
                if current != last:
                    last, changed_at = current, time.monotonic()
                if changed_at and time.monotonic() - changed_at >= .15:
                    return
                page.wait_for_timeout(50)
            except Exception:
                return  # Navigation/detachment will be reconciled by the next observation.

    def close(self):
        self.registry.invalidate()
        self.session.close()
