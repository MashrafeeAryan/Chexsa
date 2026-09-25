"""Terminal interface for Chexsa."""


def main() -> None:
    """Run the interactive Chexsa terminal session."""
    print("Chexsa")
    print("Type 'exit' or 'quit' to close Chexsa.\n")

    # Keep the terminal session alive until the user chooses to leave.
    while True:
        try:
            user_input = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        # Empty messages are ignored instead of becoming agent requests later.
        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        # Temporary behavior until requests are passed to the agent controller.
        print(f"Chexsa > Received: {user_input}")


if __name__ == "__main__":
    main()
