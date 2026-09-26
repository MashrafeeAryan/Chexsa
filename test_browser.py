from browser_state import BrowserState
from browser_actions import BrowserActions


# Connect Chexsa to the Chrome instance running with remote debugging.
browser = BrowserState()
browser.connect()

# Read the page before doing anything.
state = browser.observe()

print("URL:", state.url)
print("TITLE:", state.title)
print("ARIA:")
print(state.aria)

# BrowserActions uses the same current Chrome page.
actions = BrowserActions(browser.get_page)

# Manually perform one browser action so we can test the system without an LLM.
actions.navigate("https://github.com")

# Read the page again to confirm the browser state changed.
state = browser.observe()

print("\nAFTER ACTION")
print("URL:", state.url)
print("TITLE:", state.title)
