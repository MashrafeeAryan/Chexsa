"""Manual integration test for Chexsa's Word writing action.
It opens Word, writes a paragraph, and verifies the document contents.
Word is left open after the test so the result can be inspected."""

import sys
import time
from pathlib import Path

import win32clipboard

# Let this script import Chexsa files from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desktop_actions import DesktopActions


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


actions = DesktopActions()

print("=== WRITE IN WORD ===")
result = actions.write_word(PARAGRAPH)
print(result)

print("\n=== VERIFY TEXT ===")
actions.hotkey(["ctrl", "a"])
actions.hotkey(["ctrl", "c"])
time.sleep(0.3)

copied_text = read_clipboard().strip()
actions.press_key("right")

check(copied_text == PARAGRAPH, "Word text verification")

print("\nALL DESKTOP TESTS PASSED")
