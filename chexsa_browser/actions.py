"""Validated browser operations; all model arguments are data, never executable code."""

import time
from pathlib import Path
from urllib.parse import urlparse

from .models import ActionRequest, ActionResult, BrowserError


# Required fields, followed by optional fields. Extra fields are rejected.
FIELDS = {
    "navigate": ({"url": str}, {}), "click": ({"ref": str}, {}),
    "type": ({"ref": str, "text": str}, {"press_enter": bool}),
    "select_option": ({"ref": str, "option": str}, {}),
    "check": ({"ref": str}, {}), "uncheck": ({"ref": str}, {}),
    "press_key": ({"key": str}, {"ref": str}), "go_back": ({}, {}),
    "new_tab": ({}, {"url": str}), "close_tab": ({}, {}),
    "switch_tab": ({}, {"index": int, "page_id": str}),
    "scroll": ({}, {"amount": int, "ref": str}),
    "upload_file": ({"ref": str, "file_path": str}, {}),
    "find_elements": ({"query": str}, {"cursor": str}),
    "inspect_region": ({}, {"ref": str, "cursor": str}),
    "list_tabs": ({}, {"cursor": str}), "batch": ({"actions": list}, {}),
    "wait": ({}, {"milliseconds": int}),
    "capture_screenshot": ({}, {}),
    "click_coordinates": ({"x": (int, float), "y": (int, float), "screenshot_id": str}, {}),
    "type_focused": ({"text": str, "screenshot_id": str}, {"press_enter": bool}),
}
DISCOVERY = {"find_elements", "inspect_region", "list_tabs", "capture_screenshot"}
BATCHABLE = {"type", "select_option", "check", "uncheck", "press_key"}


def validate(request):
    if not isinstance(request, ActionRequest) or request.action not in FIELDS:
        raise BrowserError("invalid_action", "Unknown browser action.")
    if not isinstance(request.arguments, dict):
        raise BrowserError("invalid_arguments", "Action arguments must be an object.")
    if not isinstance(request.effect, dict):
        raise BrowserError("invalid_arguments", "Action effects must be an object.")
    required, optional = FIELDS[request.action]
    for name in required:
        if name not in request.arguments:
            raise BrowserError("invalid_arguments", f"{request.action} requires {name}.")
    for name, value in request.arguments.items():
        expected = {**required, **optional}.get(name)
        if expected is None or type(value) not in (expected if isinstance(expected, tuple) else (expected,)):
            raise BrowserError("invalid_arguments", f"Invalid argument {name!r} for {request.action}.")
    if request.action == "switch_tab" and len(request.arguments) != 1:
        raise BrowserError("invalid_arguments", "Choose one tab index or page_id.")
    if request.action == "batch":
        if not 1 <= len(request.arguments["actions"]) <= 10:
            raise BrowserError("invalid_arguments", "A batch must contain 1 to 10 actions.")
        for item in request.arguments["actions"]:
            if not isinstance(item, dict) or set(item) - {"action", "arguments", "effect"}:
                raise BrowserError("invalid_arguments", "Malformed batch item.")
            if not isinstance(item.get("arguments", {}), dict) or not isinstance(item.get("effect", {}), dict):
                raise BrowserError("invalid_arguments", "Batch arguments and effects must be objects.")
            if item.get("action") not in BATCHABLE:
                raise BrowserError("unsafe_batch", f"Action cannot be batched: {item.get('action')}")
            if item.get("effect", {}).get("kind") == "submission" or item.get("arguments", {}).get("press_enter") or item.get("action") == "press_key" and item.get("arguments", {}).get("key", "").lower() in ("enter", "control+enter", "ctrl+enter"):
                raise BrowserError("unsafe_batch", "Submission-capable keys must run separately.")
            validate(ActionRequest(item.get("action"), item.get("arguments", {})))


class Executor:
    def __init__(self, backend):
        self.backend = backend
        self.session = backend.session
        self.registry = backend.registry

    def execute(self, request):
        started = time.monotonic()
        executed = False
        try:
            validate(request)
            if request.action in DISCOVERY:
                observation = self.backend.observation
                if observation is None:
                    raise BrowserError("stale_observation", "Observe before inspecting the page.")
                if request.action == "find_elements":
                    data = self.backend.view.find(observation, **request.arguments)
                elif request.action == "inspect_region":
                    data = self.backend.view.inspect(observation, **request.arguments)
                elif request.action == "list_tabs":
                    data = self.backend.view.tabs(observation, **request.arguments)
                else:
                    data = self.backend.capture_screenshot()
                self.backend.view.render(observation, data)
                return ActionResult(request.action, "ok", "Observation expanded.", data=data)
            if request.action == "batch":
                return self._batch(request.arguments["actions"])
            executed = True  # Once dispatched, an exception may follow a real page-side effect.
            data = getattr(self, request.action)(**request.arguments) or {}
            return ActionResult(request.action, "ok", "Action executed; verify against the next observation.", executed=True, data={**data, "latency_ms": round((time.monotonic() - started) * 1000)})
        except BrowserError as error:
            return ActionResult(request.action, "error", str(error), error.code, executed=executed and error.code not in {"stale_target", "stale_screenshot", "stale_focus", "target_detached", "blocked", "unsupported_action", "invalid_arguments", "stale_observation"})
        except Exception as error:
            return ActionResult(request.action, "uncertain" if executed else "error", f"{type(error).__name__}: {error}", "outcome_uncertain" if executed else "execution_error", executed=executed)

    def _batch(self, actions):
        # Resolve every target before making the first change.
        for item in actions:
            ref = item.get("arguments", {}).get("ref")
            if ref:
                self.registry.resolve(ref, None if item["action"] == "press_key" else item["action"]).close()
        before = (self.session.page_id, self.session.get_page().url, dict(self.session.epochs))
        results = []
        for item in actions:
            result = self.execute(ActionRequest(item["action"], item.get("arguments", {})))
            results.append(result.__dict__)
            self.backend.wait_for_change(.4)
            after = (self.session.page_id, self.session.get_page().url, dict(self.session.epochs))
            if result.status != "ok" or before != after:
                return ActionResult("batch", "uncertain" if result.executed else "error", "Batch stopped; refresh before continuing.", "batch_interrupted", any(r["executed"] for r in results), {"results": results})
        return ActionResult("batch", "ok", "Batch executed.", executed=True, data={"results": results})

    def _click_target(self, target):
        target.client.send("DOM.scrollIntoViewIfNeeded", {"backendNodeId": target.element.node_id})
        visible = target.call("""function(){const r=this.getBoundingClientRect();if(!r.width||!r.height)return false;let root=this.getRootNode();let hit=(root.elementFromPoint?root:this.ownerDocument).elementFromPoint(r.x+r.width/2,r.y+r.height/2);return hit===this||this.contains(hit);}""")
        if not visible:
            raise BrowserError("blocked", "The control is covered or has no visible click point.")
        quads = target.client.send("DOM.getContentQuads", {"backendNodeId": target.element.node_id}).get("quads", [])
        if not quads:
            raise BrowserError("blocked", "No visible geometry is available for the control.")
        quad = quads[0]
        x, y = sum(quad[0::2]) / 4, sum(quad[1::2]) / 4
        for kind in ("mousePressed", "mouseReleased"):
            target.client.send("Input.dispatchMouseEvent", {"type": kind, "x": x, "y": y, "button": "left", "clickCount": 1})

    def click(self, ref):
        target = self.registry.resolve(ref, "click")
        try:
            self._click_target(target)
        finally:
            target.close()

    def click_coordinates(self, x, y, screenshot_id):
        return self.backend.visual.click(x, y, screenshot_id)

    def type_focused(self, text, screenshot_id, press_enter=False):
        return self.backend.visual.type(text, screenshot_id, press_enter)

    def type(self, ref, text, press_enter=False):
        target = self.registry.resolve(ref, "type")
        try:
            target.client.send("DOM.focus", {"backendNodeId": target.element.node_id})
            if not target.details()["focused"]:
                raise BrowserError("blocked", "The requested field did not receive focus.")
            self.session.get_page().keyboard.press("ControlOrMeta+A")
            target.client.send("Input.insertText", {"text": text})
            actual = target.details()["value"]
            if actual.replace("\r\n", "\n").strip() != text.replace("\r\n", "\n").strip():
                raise BrowserError("verification_failed", "The field's value does not match the requested text.")
            if press_enter:
                self.session.get_page().keyboard.press("Enter")
            return {"verified": True, "value": actual, "ref": ref}
        finally:
            target.close()

    def select_option(self, ref, option):
        target = self.registry.resolve(ref, "select_option")
        try:
            selected = target.call("""function(label){const option=Array.from(this.options).find(o=>o.label===label);if(!option||option.disabled)throw Error('Option unavailable');this.value=option.value;this.dispatchEvent(new Event('input',{bubbles:true}));this.dispatchEvent(new Event('change',{bubbles:true}));return this.selectedOptions[0].label;}""", option)
            if selected != option:
                raise BrowserError("verification_failed", "The requested option was not selected.")
            return {"verified": True, "option": selected}
        finally:
            target.close()

    def _toggle(self, ref, checked):
        target = self.registry.resolve(ref, "check" if checked else "uncheck")
        try:
            state = target.details()["checked"] in (True, "true")
            if state != checked:
                self._click_target(target)
            if (target.details()["checked"] in (True, "true")) != checked:
                raise BrowserError("verification_failed", "The control did not reach the requested checked state.")
            return {"verified": True, "checked": checked}
        finally:
            target.close()

    def check(self, ref):
        return self._toggle(ref, True)

    def uncheck(self, ref):
        return self._toggle(ref, False)

    def press_key(self, key, ref=None):
        if ref:
            target = self.registry.resolve(ref)
            try:
                target.client.send("DOM.focus", {"backendNodeId": target.element.node_id})
                if not target.details()["focused"]:
                    raise BrowserError("blocked", "The requested control did not receive focus.")
            finally:
                target.close()
        self.session.get_page().keyboard.press(key)

    def navigate(self, url):
        if urlparse(url).scheme not in ("http", "https", "about", "file"):
            raise BrowserError("invalid_arguments", "Unsupported navigation URL scheme.")
        self.registry.invalidate()
        self.session.get_page().goto(url, wait_until="domcontentloaded", timeout=30000)

    def go_back(self):
        self.registry.invalidate()
        self.session.get_page().go_back(wait_until="commit", timeout=10000)

    def wait(self, milliseconds=500):
        if not 0 <= milliseconds <= 5000:
            raise BrowserError("invalid_arguments", "Wait must be between 0 and 5000 milliseconds.")
        self.session.get_page().wait_for_timeout(milliseconds)

    def new_tab(self, url="about:blank"):
        if urlparse(url).scheme not in ("http", "https", "about", "file"):
            raise BrowserError("invalid_arguments", "Unsupported navigation URL scheme.")
        page = self.session.get_page().context.new_page()
        self.session.select(page)
        self.navigate(url)

    def switch_tab(self, index=None, page_id=None):
        observation = self.backend.observation
        tabs = observation.tabs if observation else []
        chosen = next((tab for tab in tabs if tab["page_id"] == page_id), None) if page_id else (tabs[index] if index is not None and 0 <= index < len(tabs) else None)
        if chosen is None:
            raise BrowserError("invalid_arguments", "Unknown tab. Observe the tabs again.")
        page = next((p for p in self.session.pages() if self.session.page_identifier(p) == chosen["page_id"]), None)
        if page is None:
            raise BrowserError("stale_target", "The requested tab has closed.")
        self.registry.invalidate()
        self.session.select(page)
        page.bring_to_front()

    def close_tab(self):
        pages = self.session.pages()
        if len(pages) <= 1:
            raise BrowserError("blocked", "Cannot close the only open tab.")
        current = self.session.get_page()
        self.registry.invalidate()
        current.close()
        self.session.select(next(page for page in reversed(pages) if page != current))
        self.session.get_page().bring_to_front()

    def scroll(self, amount=600, ref=None):
        if ref:
            target = self.registry.resolve(ref)
            try:
                target.call("function(amount){this.scrollBy(0,amount);}", amount)
            finally:
                target.close()
        else:
            self.session.get_page().mouse.wheel(0, amount)

    def upload_file(self, ref, file_path):
        path = Path(file_path).expanduser().resolve()
        if not path.is_file():
            raise BrowserError("invalid_arguments", "The upload file does not exist.")
        target = self.registry.resolve(ref, "upload_file")
        try:
            target.client.send("DOM.setFileInputFiles", {"backendNodeId": target.element.node_id, "files": [str(path)]})
            names = target.call("function(){return Array.from(this.files).map(f=>f.name);}")
            if path.name not in names:
                raise BrowserError("verification_failed", "The browser did not select the upload file.")
            return {"verified": True, "files": names}
        finally:
            target.close()
