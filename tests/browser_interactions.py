"""Manual browser integration test for typing and clicking."""

import sys
from pathlib import Path

# Let this script import Chexsa's source files from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from browser_actions import BrowserActions
from browser_state import BrowserState


browser = BrowserState()
browser.connect()

page = browser.get_page()
actions = BrowserActions(browser.get_page)

# Use a tiny local page so this test does not depend on a real website.
page.set_content(
    """
    <label for="message">Message</label>
    <input id="message">

    <button onclick="document.body.dataset.clicked='yes'">
        Submit
    </button>
    """
)

print("BEFORE ACTIONS")
print("Text:", page.get_by_role("textbox", name="Message").input_value())
print("Clicked:", page.locator("body").get_attribute("data-clicked"))

# Type into the textbox using the same role/name targeting Chexsa will use later.
actions.type_text(
    role="textbox",
    name="Message",
    text="Hello from Chexsa",
)

# Click the button using its ARIA role and name.
actions.click(
    role="button",
    name="Submit",
)

print("\nAFTER ACTIONS")
print("Text:", page.get_by_role("textbox", name="Message").input_value())
print("Clicked:", page.locator("body").get_attribute("data-clicked"))
