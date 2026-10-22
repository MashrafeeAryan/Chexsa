"""Visual actions are scoped to a real screenshot and a verified focus identity."""

import hashlib
import uuid

from .models import BrowserError


OPTIONS = {"type": "jpeg", "quality": 55, "full_page": False, "scale": "css", "animations": "disabled", "caret": "hide"}
ACTIVE = """(() => {let e=document.activeElement;for(let i=0;e&&i<20;i++){if(e.shadowRoot?.activeElement)e=e.shadowRoot.activeElement;else if(e.tagName==='IFRAME'&&e.contentDocument?.activeElement)e=e.contentDocument.activeElement;else break;}return e;})()"""


class VisualTargeting:
    def __init__(self, backend):
        self.backend = backend
        self.ticket = None
        self.focus_ticket = None

    def _viewport(self):
        return self.backend.session.get_page().evaluate("({width:innerWidth,height:innerHeight,x:scrollX,y:scrollY,dpr:devicePixelRatio,version:window.__chexsaWatch?.version})")

    def _settled_image(self):
        # Initial high-DPI screenshots can precede Chrome's final compositor paint.
        # Keep capture bounded on dynamic pages; clicking still requires an exact match.
        page = self.backend.session.get_page()
        previous = None
        for _ in range(4):
            image = page.screenshot(**OPTIONS)
            viewport = self._viewport()
            # Playwright's temporary caret styles increment the mutation counter.
            rendered = (image, {key: value for key, value in viewport.items() if key != "version"})
            if rendered == previous:
                break
            previous = rendered
        return image, viewport

    def capture(self):
        observation = self.backend.observation
        if observation is None:
            raise BrowserError("stale_observation", "Observe before taking a screenshot.")
        image, viewport = self._settled_image()
        screenshot_id = uuid.uuid4().hex
        self.ticket = {"id": screenshot_id, "observation": observation.id, "page": self.backend.session.page_id, "epochs": dict(self.backend.session.epochs), "viewport": viewport, "digest": hashlib.sha256(image).hexdigest()}
        observation.screenshot, observation.screenshot_id = image, screenshot_id
        if self.backend.trace_screenshots and self.backend.task_journal:
            directory = self.backend.task_journal.path.parent / "screenshots"
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"{screenshot_id}.jpg").write_bytes(image)
        metadata = {"screenshot_id": screenshot_id, "width": self.ticket["viewport"]["width"], "height": self.ticket["viewport"]["height"], "coordinate_space": "CSS pixels, viewport origin"}
        self.backend.view.render(observation, metadata)
        return metadata

    def _check(self, screenshot_id):
        session = self.backend.session
        ticket = self.ticket
        if not ticket or ticket["id"] != screenshot_id or ticket["observation"] != self.backend.observation.id or ticket["page"] != session.page_id or ticket["epochs"] != session.epochs or ticket["viewport"] != self._viewport():
            raise BrowserError("stale_screenshot", "The screenshot is stale. Capture a new one before clicking.")
        # Catches canvas/image changes and CSS animation that DOM mutation counters miss.
        current = session.get_page().screenshot(**OPTIONS)
        if hashlib.sha256(current).hexdigest() != ticket["digest"]:
            raise BrowserError("stale_screenshot", "The visible page changed. Capture a new screenshot.")
        return ticket

    def _focus(self):
        session = self.backend.session
        for target_id, client in reversed(session.targets()):
            remote = client.send("Runtime.evaluate", {"expression": ACTIVE})
            object_id = remote.get("result", {}).get("objectId")
            if not object_id:
                continue
            try:
                info = client.send("Runtime.callFunctionOn", {"objectId": object_id, "functionDeclaration": "function(){return {editable:this.isContentEditable||this.tagName==='TEXTAREA'||this.tagName==='INPUT'&&!['button','submit','checkbox','radio','file','hidden'].includes(this.type),focused:this.ownerDocument.hasFocus(),disabled:!!this.disabled,readonly:!!this.readOnly,value:this.value===undefined?this.innerText:this.value};}", "returnByValue": True})["result"].get("value", {})
                if info.get("editable") and info.get("focused") and not info.get("disabled") and not info.get("readonly"):
                    node = client.send("DOM.describeNode", {"objectId": object_id})["node"]
                    return target_id, node["backendNodeId"], client, info
            finally:
                client.send("Runtime.releaseObject", {"objectId": object_id})
        return None

    def click(self, x, y, screenshot_id):
        ticket = self._check(screenshot_id)
        viewport = ticket["viewport"]
        if not 0 <= x < viewport["width"] or not 0 <= y < viewport["height"]:
            raise BrowserError("invalid_arguments", "Coordinates are outside the screenshot viewport.")
        self.backend.session.get_page().mouse.click(x, y)
        focused = self._focus()
        self.focus_ticket = {"screenshot": screenshot_id, "page": ticket["page"], "epochs": dict(self.backend.session.epochs), "identity": focused[:2]} if focused else None
        self.ticket = None  # The click consumes the screenshot's authority for pointer actions.
        return {"source_screenshot": screenshot_id, "editable_focused": bool(focused)}

    def type(self, text, screenshot_id, press_enter=False):
        ticket = self.focus_ticket
        session = self.backend.session
        focused = self._focus()
        if not ticket or not focused or ticket["screenshot"] != screenshot_id or ticket["page"] != session.page_id or ticket["epochs"] != session.epochs or ticket["identity"] != focused[:2]:
            raise BrowserError("stale_focus", "The clicked editable field no longer has focus. Observe and target it again.")
        session.get_page().keyboard.press("ControlOrMeta+A")
        focused[2].send("Input.insertText", {"text": text})
        after = self._focus()
        if not after or after[:2] != focused[:2] or after[3]["value"].replace("\r\n", "\n").strip() != text.replace("\r\n", "\n").strip():
            raise BrowserError("verification_failed", "Visual typing could not be verified against the actual field.")
        if press_enter:
            session.get_page().keyboard.press("Enter")
        self.focus_ticket = None
        return {"verified": True, "source_screenshot": screenshot_id}
