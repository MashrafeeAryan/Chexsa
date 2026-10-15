"""Run Chexsa from the terminal."""

from agent import Agent
from browser_actions import BrowserActions
from browser_state import BrowserState
from llm import LLM


def main() -> None:
    """Start Chexsa and run the terminal session."""

    print("Chexsa")
    print("Type 'exit' or 'quit' to close Chexsa.\n")

    browser = BrowserState()
    browser.connect()

    actions = BrowserActions(
        browser.get_page,
        browser.set_page,
    )

    llm = LLM()

    agent = Agent(
        observe=browser.observe,
        decide=llm.decide,
        execute=actions.execute,
    )

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
