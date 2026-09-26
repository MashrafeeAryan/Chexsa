"""Terminal interface for Chexsa."""

from agent import Agent


def main() -> None:
    """Run the interactive Chexsa terminal session."""
    print("Chexsa")
    print("Type 'exit' or 'quit' to close Chexsa.\n")

    # Create one agent for the whole session so future state can live here.
    agent = Agent()

    # Keep the terminal session alive until the user chooses to leave.
    while True:
        try:
            user_input = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        # Empty messages should not become agent requests.
        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        response = agent.run(user_input)
        print(f"Chexsa > {response}")


if __name__ == "__main__":
    main()
