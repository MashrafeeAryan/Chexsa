"""Own a CDP connection without closing the user's browser on disconnect."""

import os
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

from .models import BrowserError


class BrowserSession:
    def __init__(self, cdp_url="http://127.0.0.1:9222", auto_launch=False):
        self.cdp_url = cdp_url
        self.auto_launch = auto_launch
        self.playwright = None
        self.browser = None
        self.page = None
        self.page_id = ""
        self.clients = {}
        self.epochs = {}
        self._frame_clients = {}
        self._page_ids = {}

    def connect(self):
        if self.browser:
            return
        self.playwright = sync_playwright().start()
        try:
            self.browser = self.playwright.chromium.connect_over_cdp(self.cdp_url)
        except Exception:
            if not self.auto_launch:
                self.close()
                raise BrowserError("not_connected", "Start Chrome with CDP on port 9222, or enable auto launch.")
            self._launch()
            self.browser = self.playwright.chromium.connect_over_cdp(self.cdp_url)
        pages = [p for context in self.browser.contexts for p in context.pages]
        if not pages:
            self.page = self.browser.contexts[0].new_page()
        else:
            self.page = next((p for p in pages if p.evaluate("document.hasFocus()")), pages[-1])
        self.select(self.page)

    def _launch(self):
        parsed = urlparse(self.cdp_url)
        if parsed.hostname not in ("localhost", "127.0.0.1"):
            raise BrowserError("not_connected", "Auto launch only supports local Chrome.")
        candidates = [shutil.which("chrome"), str(Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe"), str(Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Google/Chrome/Application/chrome.exe")]
        executable = next((p for p in candidates if p and Path(p).exists()), None)
        if not executable:
            raise BrowserError("not_connected", "Chrome was not found.")
        profile = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Chexsa" / "chrome"
        profile.mkdir(parents=True, exist_ok=True)
        subprocess.Popen([executable, f"--remote-debugging-port={parsed.port or 9222}", f"--user-data-dir={profile}"], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                with urlopen(self.cdp_url + "/json/version", timeout=1):
                    return
            except OSError:
                time.sleep(.2)
        raise BrowserError("not_connected", "Chrome did not become available within 15 seconds.")

    def get_page(self):
        if self.page is None or self.page.is_closed():
            raise BrowserError("page_closed", "The observed tab is closed. Select an open tab.")
        return self.page

    def select(self, page):
        self.page = page
        self.page_id = self.page_identifier(page)

    def page_identifier(self, page):
        if page not in self._page_ids:
            client = page.context.new_cdp_session(page)
            target = client.send("Target.getTargetInfo")["targetInfo"]["targetId"]
            self._page_ids[page] = target
            self._remember(target, client)
        return self._page_ids[page]

    def _remember(self, target, client):
        if target in self.clients:
            try:
                self.clients[target].send("Target.getTargetInfo")
                client.detach()
                return
            except Exception:
                self.clients.pop(target, None)
        self.clients[target] = client
        self.epochs[target] = 0
        client.send("Page.enable")
        client.on("Page.frameNavigated", lambda event: self._changed(target))
        client.on("Page.frameDetached", lambda event: self._changed(target))

    def _changed(self, target):
        self.epochs[target] = self.epochs.get(target, 0) + 1

    def targets(self):
        page = self.get_page()
        found = {self.page_id}
        previous = set(self._frame_clients.values())
        current = {}
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            try:
                # A Frame can move to a different renderer/CDP target on navigation.
                client = page.context.new_cdp_session(frame)
                target = client.send("Target.getTargetInfo")["targetInfo"]["targetId"]
                current[frame] = target
                self._remember(target, client)
                found.add(target)
            except Exception:
                # Same-process frames are already in the parent target's snapshot.
                pass
        self._frame_clients = current
        for obsolete in previous - found - set(self._page_ids.values()):
            old = self.clients.pop(obsolete, None)
            self.epochs.pop(obsolete, None)
            if old:
                try:
                    old.detach()
                except Exception:
                    pass
        return [(target, self.clients[target]) for target in sorted(found)]

    def tabs(self):
        return [{"index": i, "page_id": self.page_identifier(page), "title": page.title(), "url": page.url} for i, page in enumerate(self.pages())]

    def pages(self):
        for page, target in list(self._page_ids.items()):
            if page.is_closed():
                self._page_ids.pop(page)
                self.clients.pop(target, None)
                self.epochs.pop(target, None)
        return [page for context in self.browser.contexts for page in context.pages if not page.is_closed()]

    def close(self):
        if self.playwright:
            self.playwright.stop()
        self.playwright = self.browser = self.page = None
        self.clients.clear()
        self._frame_clients.clear()
        self._page_ids.clear()
