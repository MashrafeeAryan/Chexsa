"""Terminal interface for FridayV2."""


def main() -> None:
    """Run the interactive FridayV2 terminal session."""
    print("FridayV2")
    print("Type 'exit' or 'quit' to close Friday.\n")

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

        print(f"Friday > Received: {user_input}")


if __name__ == "__main__":
    main()
