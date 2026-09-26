"""Starts Chexsa and connects the parts needed to run it.
It connects the browser, LLM, and agent before reading user commands.
This is the main file users interact with from the terminal."""

from agent import Agent
from browser_actions import BrowserActions
from browser_state import BrowserState
from llm import GeminiLLM


def main() -> None:
    """Start Chexsa and run the terminal session."""

    print("Chexsa")
    print("Type 'exit' or 'quit' to close Chexsa.\n")

    # Connect Chexsa to the Chrome instance running on port 9222.
    browser = BrowserState()
    browser.connect()

    # BrowserActions controls the same Chrome page BrowserState reads.
    actions = BrowserActions(browser.get_page)

    # Gemini decides which browser action should happen next.
    llm = GeminiLLM()

    # Connect the browser, LLM, and actions to the main agent loop.
    agent = Agent(
        observe=browser.observe,
        decide=llm.decide,
        execute=actions.execute,
    )

    # Keep accepting requests until the user exits.
    while True:
        try:
            user_input = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        response = agent.run(user_input)
        print(f"Chexsa > {response}")


if __name__ == "__main__":
    main()
