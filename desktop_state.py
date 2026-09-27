"""Reads the current Windows desktop state for Chexsa.
It finds the active window, open windows, and useful UI Automation controls.
It only observes the desktop and never performs actions."""

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from pywinauto import Desktop


USEFUL_CONTROL_TYPES = {
    "Button",
    "Edit",
    "Document",
    "ComboBox",
    "CheckBox",
    "RadioButton",
    "MenuItem",
    "TabItem",
    "ListItem",
    "TreeItem",
    "Hyperlink",
}


@dataclass
class DesktopSnapshot:
    """A compact description of the current Windows desktop."""

    active_window: str
    windows: list[str]
    controls: list[str]


class DesktopState:
    """Read useful desktop information through Windows UI Automation."""

    def __init__(
        self,
        max_controls: int = 100,
        max_name_chars: int = 120,
    ) -> None:
        self.desktop = Desktop(backend="uia")
        self.max_controls = max_controls
        self.max_name_chars = max_name_chars

    def observe(self) -> DesktopSnapshot:
        """Read the current desktop state."""

        total_start = perf_counter()

        active = self._get_active_window()
        windows = self._get_windows()
        controls = self._get_controls(active)

        active_window = self._get_name(active)

        print(
            f"[TIMER] Desktop observe total: "
            f"{perf_counter() - total_start:.2f}s"
        )

        return DesktopSnapshot(
            active_window=active_window,
            windows=windows,
            controls=controls,
        )

    def _get_active_window(self) -> Any:
        """Find the currently active top-level window."""

        start = perf_counter()

        active = self.desktop.get_active().top_level_parent()

        print(
            f"[TIMER] Desktop active window: "
            f"{perf_counter() - start:.2f}s"
        )

        return active

    def _get_windows(self) -> list[str]:
        """List visible top-level windows."""

        start = perf_counter()
        windows = []

        for window in self.desktop.windows(visible_only=True):
            name = self._get_name(window)

            if name:
                windows.append(name)

        print(
            f"[TIMER] Desktop windows: "
            f"{perf_counter() - start:.2f}s"
        )

        return windows

    def _get_controls(self, active_window: Any) -> list[str]:
        """Read useful controls from the active window."""

        start = perf_counter()
        controls = []
        seen = set()

        try:
            descendants = active_window.descendants()
        except Exception:
            descendants = []

        for control in descendants:
            try:
                info = control.element_info
                control_type = info.control_type

                if control_type not in USEFUL_CONTROL_TYPES:
                    continue

                if not info.visible:
                    continue

                name = (info.name or "").strip()
                auto_id = (info.auto_id or "").strip()

                # Avoid sending huge control names to the LLM.
                name = name[: self.max_name_chars]

                if name:
                    description = f'{control_type} "{name}"'
                elif auto_id:
                    description = f'{control_type} [id="{auto_id}"]'
                else:
                    continue

                # UI Automation sometimes exposes duplicate controls.
                if description in seen:
                    continue

                seen.add(description)
                controls.append(description)

                if len(controls) >= self.max_controls:
                    break

            except Exception:
                continue

        print(
            f"[TIMER] Desktop controls: "
            f"{perf_counter() - start:.2f}s"
        )

        return controls

    def _get_name(self, control: Any) -> str:
        """Get a short readable name for a UI element."""

        try:
            name = control.window_text().strip()
        except Exception:
            name = ""

        return name[: self.max_name_chars]
