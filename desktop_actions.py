"""Performs Windows desktop actions for Chexsa.
It uses UI Automation to work with windows and controls without screen coordinates.
It only executes actions and does not decide what to do."""

from time import perf_counter
from typing import Any

from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys


KEY_NAMES = {
    "enter": "{ENTER}",
    "escape": "{ESC}",
    "tab": "{TAB}",
    "backspace": "{BACKSPACE}",
    "delete": "{DELETE}",
    "up": "{UP}",
    "down": "{DOWN}",
    "left": "{LEFT}",
    "right": "{RIGHT}",
}


class DesktopActions:
    """Perform actions on Windows applications through UI Automation."""

    def __init__(self) -> None:
        self.desktop = Desktop(backend="uia")

    def execute(
        self,
        action: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Send an action name to the correct desktop function."""

        actions = {
            "launch_app": self.launch_app,
            "focus_window": self.focus_window,
            "click_control": self.click_control,
            "type_text": self.type_text,
            "press_key": self.press_key,
            "hotkey": self.hotkey,
            "select_option": self.select_option,
            "check": self.check,
            "uncheck": self.uncheck,
            "close_window": self.close_window,
        }

        if action not in actions:
            raise ValueError(f"Unknown desktop action: {action}")

        start = perf_counter()
        result = actions[action](**arguments)

        print(
            f"[TIMER] Desktop action {action}: "
            f"{perf_counter() - start:.2f}s"
        )

        return result

    def launch_app(self, command: str) -> str:
        """Launch a Windows application."""

        Application(backend="uia").start(command)

        return f"Launched {command}"

    def focus_window(self, title: str) -> str:
        """Bring a window to the foreground."""

        window = self._get_window(title)
        window.set_focus()

        return f'Focused window "{title}"'

    def click_control(
        self,
        control_type: str,
        name: str | None = None,
        auto_id: str | None = None,
        window_title: str | None = None,
    ) -> str:
        """Click a UI Automation control."""

        control = self._get_control(
            control_type,
            name,
            auto_id,
            window_title,
        )

        control.click_input()

        return f'Clicked {control_type} "{name or auto_id}"'

    def type_text(
        self,
        control_type: str,
        text: str,
        name: str | None = None,
        auto_id: str | None = None,
        window_title: str | None = None,
    ) -> str:
        """Type text into a UI Automation control."""

        control = self._get_control(
            control_type,
            name,
            auto_id,
            window_title,
        )

        control.set_focus()

        # Edit controls can usually set text directly.
        if hasattr(control, "set_edit_text"):
            control.set_edit_text(text)
        else:
            control.type_keys(
                text,
                with_spaces=True,
                set_foreground=True,
            )

        return f'Entered text into {control_type} "{name or auto_id}"'

    def press_key(self, key: str) -> str:
        """Press one keyboard key."""

        key_code = KEY_NAMES.get(key.lower(), key)
        send_keys(key_code)

        return f"Pressed {key}"

    def hotkey(self, keys: list[str]) -> str:
        """Press a keyboard shortcut such as Ctrl+S."""

        if len(keys) < 2:
            raise ValueError("A hotkey needs at least two keys.")

        modifiers = {
            "ctrl": "^",
            "alt": "%",
            "shift": "+",
        }

        prefix = ""
        for key in keys[:-1]:
            key_name = key.lower()

            if key_name not in modifiers:
                raise ValueError(f"Unsupported modifier: {key}")

            prefix += modifiers[key_name]

        final_key = KEY_NAMES.get(
            keys[-1].lower(),
            keys[-1],
        )

        send_keys(prefix + final_key)

        return f'Pressed hotkey {"+".join(keys)}'

    def select_option(
        self,
        name: str,
        option: str,
        window_title: str | None = None,
    ) -> str:
        """Choose an option from a ComboBox."""

        control = self._get_control(
            "ComboBox",
            name,
            window_title=window_title,
        )

        control.select(option)

        return f'Selected "{option}" from "{name}"'

    def check(
        self,
        name: str,
        window_title: str | None = None,
    ) -> str:
        """Check a checkbox."""

        control = self._get_control(
            "CheckBox",
            name,
            window_title=window_title,
        )

        if control.get_toggle_state() != 1:
            control.toggle()

        return f'Checked "{name}"'

    def uncheck(
        self,
        name: str,
        window_title: str | None = None,
    ) -> str:
        """Uncheck a checkbox."""

        control = self._get_control(
            "CheckBox",
            name,
            window_title=window_title,
        )

        if control.get_toggle_state() != 0:
            control.toggle()

        return f'Unchecked "{name}"'

    def close_window(self, title: str | None = None) -> str:
        """Close a desktop window."""

        window = self._get_window(title)
        window.close()

        return f'Closed window "{title or "active window"}"'

    def _get_window(self, title: str | None = None):
        """Find a top-level window."""

        if title:
            return self.desktop.window(title=title).wrapper_object()

        return self.desktop.get_active().top_level_parent()

    def _get_control(
        self,
        control_type: str,
        name: str | None = None,
        auto_id: str | None = None,
        window_title: str | None = None,
    ):
        """Find a control inside a window."""

        if not name and not auto_id:
            raise ValueError(
                "A control needs either a name or automation ID."
            )

        window = self._get_window(window_title)

        criteria = {
            "control_type": control_type,
        }

        if name:
            criteria["title"] = name

        if auto_id:
            criteria["auto_id"] = auto_id

        return window.child_window(
            **criteria
        ).wrapper_object()
