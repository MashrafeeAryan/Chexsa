"""Manual browser integration test for Chexsa."""

import sys
from pathlib import Path

# Let this script import Chexsa's source files from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from browser_actions import BrowserActions
from browser_state import BrowserState


def check(condition: bool, name: str) -> None:
    """Print a simple result and stop if a test fails."""

    if condition:
        print(f"{name}: PASS")
        return

    print(f"{name}: FAIL")
    raise RuntimeError(f"{name} failed")


browser = BrowserState()
browser.connect()
actions = BrowserActions(browser.get_page)

print("=== OBSERVATION TEST ===")
before = browser.observe()
print("URL:", before.url)
print("TITLE:", before.title)

print("\n=== NAVIGATION TEST ===")
actions.navigate("https://github.com")

after = browser.observe()
print("URL:", after.url)
print("TITLE:", after.title)

check("github.com" in after.url, "Navigation")

print("\n=== INTERACTION TEST ===")
page = browser.get_page()

# Use a tiny local page so this test does not depend on a real website.
page.set_content(
    """
    <label for="message">Message</label>
    <input id="message">

    <button onclick="document.getElementById('result').textContent='Clicked!'">
        Submit
    </button>

    <p id="result">Not clicked</p>
    """
)

# Show what BrowserState sees before we interact with the page.
interaction_state = browser.observe()
print("ARIA:")
print(interaction_state.aria)

actions.type_text(
    role="textbox",
    name="Message",
    text="Hello from Chexsa",
)

actions.click(
    role="button",
    name="Submit",
)

typed_text = page.get_by_role("textbox", name="Message").input_value()
click_result = page.locator("#result").inner_text()

print("\nTextbox:", typed_text)
print("Button result:", click_result)

check(typed_text == "Hello from Chexsa", "Typing")
check(click_result == "Clicked!", "Clicking")

print("\nALL BROWSER TESTS PASSED")
