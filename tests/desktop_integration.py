"""Integration test for Chexsa's Windows desktop state and actions.
It opens Microsoft Word, writes a four-sentence paragraph, and verifies the text.
Word is left open after the test so the result can be inspected."""

import sys
import time
from pathlib import Path

import win32clipboard

# Let this script import Chexsa files from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desktop_actions import DesktopActions
from desktop_state import DesktopSnapshot, DesktopState


PARAGRAPH = (
    "Artificial intelligence can help people complete repetitive tasks more quickly. "
    "It can support better decisions by finding useful patterns in large amounts of information. "
    "AI can also improve accessibility by helping people communicate, learn, and use technology in new ways. "
    "When it is designed responsibly, AI can give people more time to focus on creative and meaningful work."
)


def check(condition: bool, name: str) -> None:
    """Print a simple result and stop if a test fails."""

    if condition:
        print(f"{name}: PASS")
        return

    print(f"{name}: FAIL")
    raise RuntimeError(f"{name} failed")


def wait_for_word(
    state: DesktopState,
    actions: DesktopActions,
    timeout: float = 20.0,
) -> str:
    """Wait for a Word window and return its exact title."""

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        snapshot = state.observe()

        for title in snapshot.windows:
            if "word" in title.lower():
                actions.focus_window(title)
                time.sleep(1)
                return title

        time.sleep(0.5)

    raise RuntimeError("Microsoft Word did not appear within 20 seconds.")


def find_editable_control(
    snapshot: DesktopSnapshot,
) -> tuple[str, str | None, str | None]:
    """Find a Document or Edit control from the desktop state."""

    for control_type in ("Document", "Edit"):
        prefix = f"{control_type} "

        for description in snapshot.controls:
            if not description.startswith(prefix):
                continue

            value = description[len(prefix):]

            if value.startswith('"') and value.endswith('"'):
                return control_type, value[1:-1], None

            if value.startswith('[id="') and value.endswith('"]'):
                return control_type, None, value[5:-2]

    raise RuntimeError(
        "Word opened, but no editable Document or Edit control was found."
    )


def read_clipboard() -> str:
    """Read Unicode text from the Windows clipboard."""

    for _ in range(10):
        try:
            win32clipboard.OpenClipboard()

            try:
                return win32clipboard.GetClipboardData(
                    win32clipboard.CF_UNICODETEXT
                )
            finally:
                win32clipboard.CloseClipboard()

        except Exception:
            time.sleep(0.1)

    raise RuntimeError("Could not read text from the Windows clipboard.")


state = DesktopState()
actions = DesktopActions()

print("=== LAUNCH WORD ===")

# Use Windows shell lookup so this works with normal Office installs.
actions.launch_app('cmd.exe /c start "" winword /w')

word_title = wait_for_word(state, actions)
print("Word window:", word_title)
check("word" in word_title.lower(), "Word launch")

print("\n=== DESKTOP STATE ===")

snapshot = state.observe()
print("Active window:", snapshot.active_window)
print("Controls:")

for control in snapshot.controls:
    print(" ", control)

control_type, name, auto_id = find_editable_control(snapshot)

print("\nEditable control:", control_type, name or auto_id)
check(control_type in {"Document", "Edit"}, "Editable control detection")

print("\n=== TYPE PARAGRAPH ===")

actions.type_text(
    control_type=control_type,
    name=name,
    auto_id=auto_id,
    window_title=word_title,
    text=PARAGRAPH,
)

print(PARAGRAPH)

print("\n=== VERIFY TEXT ===")

# Copy the document contents so the test can verify what Word received.
actions.hotkey(["ctrl", "a"])
actions.hotkey(["ctrl", "c"])
time.sleep(0.3)

copied_text = read_clipboard().strip()

# Remove selection while leaving the document open.
actions.press_key("right")

check(copied_text == PARAGRAPH, "Paragraph verification")

print("\nALL DESKTOP TESTS PASSED")
