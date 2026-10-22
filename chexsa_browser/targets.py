"""Observation-local refs resolve recorded CDP nodes, never nth name matches."""

from dataclasses import dataclass

from .models import BrowserError


DETAILS = """function() { return {
 connected: this.isConnected && !!this.ownerDocument.defaultView,
 tag: this.tagName, type: this.type, disabled: !!this.disabled || this.getAttribute('aria-disabled') === 'true',
 readonly: !!this.readOnly || this.getAttribute('aria-readonly') === 'true',
 value: this.value === undefined ? (this.innerText || this.textContent || '') : this.value,
 checked: this.checked === undefined ? this.getAttribute('aria-checked') : this.checked,
 focused: this === this.ownerDocument.activeElement || !!(this.getRootNode().activeElement === this)
}; }"""


@dataclass
class Target:
    client: object
    object_id: str
    element: object

    def call(self, function, *arguments):
        result = self.client.send("Runtime.callFunctionOn", {"objectId": self.object_id, "functionDeclaration": function, "arguments": [{"value": value} for value in arguments], "returnByValue": True})
        if result.get("exceptionDetails"):
            raise BrowserError("execution_error", "The browser rejected the element operation.")
        return result.get("result", {}).get("value")

    def details(self):
        return self.call(DETAILS)

    def close(self):
        try:
            self.client.send("Runtime.releaseObject", {"objectId": self.object_id})
        except Exception:
            pass


class TargetRegistry:
    def __init__(self, session):
        self.session = session
        self.counter = 0
        self.refs = {}
        self.page_id = ""
        self.epochs = {}

    def invalidate(self):
        self.refs.clear()

    def bind(self, elements):
        self.invalidate()
        self.page_id = self.session.page_id
        self.epochs = dict(self.session.epochs)
        for element in elements:
            self.counter += 1
            element.ref = f"e{self.counter}"
            self.refs[element.ref] = element

    def resolve(self, ref, capability=None):
        element = self.refs.get(ref)
        if element is None:
            raise BrowserError("stale_target", f"Unknown or stale ref {ref!r}. Observe again.")
        if self.page_id != self.session.page_id:
            raise BrowserError("stale_target", "This ref belongs to another tab. Observe again.")
        client = self.session.clients.get(element.target_id)
        if client is None or self.epochs.get(element.target_id) != self.session.epochs.get(element.target_id):
            raise BrowserError("stale_target", "The document changed. Observe again.")
        if capability and capability not in element.capabilities:
            raise BrowserError("unsupported_action", f"{element.role} does not support {capability}.")
        try:
            remote = client.send("DOM.resolveNode", {"backendNodeId": element.node_id, "objectGroup": "chexsa"})
            object_id = remote.get("object", {}).get("objectId")
            if not object_id:
                raise BrowserError("target_detached", "The observed element no longer exists.")
            target = Target(client, object_id, element)
            details = target.details()
            if not details or not details["connected"]:
                target.close()
                raise BrowserError("target_detached", "The observed element was detached. Observe again.")
            if capability and (details["disabled"] or capability == "type" and details["readonly"]):
                target.close()
                raise BrowserError("blocked", "The observed control is disabled or read-only.")
            if capability and "_ax_role" in element.states:
                current = client.send("Accessibility.getPartialAXTree", {"backendNodeId": element.node_id}).get("nodes", [])
                ax = next((node for node in current if node.get("backendDOMNodeId") == element.node_id), None)
                if not ax or ax.get("ignored") or ax.get("role", {}).get("value", "").lower() != element.states["_ax_role"] or ax.get("name", {}).get("value", "") != element.states["_ax_name"]:
                    target.close()
                    raise BrowserError("stale_target", "The control's role or accessible name changed. Observe again.")
            return target
        except BrowserError:
            raise
        except Exception as error:
            raise BrowserError("target_detached", "The browser could not resolve the recorded node. Observe again.") from error
