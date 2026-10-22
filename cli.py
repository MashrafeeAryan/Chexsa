"""Terminal entry point for the verified browser engine."""

import argparse

from chexsa_browser.journal import TaskJournal
from chexsa_browser.runtime import create_browser_agent
from llm import LLM


def main(argv=None):
    parser = argparse.ArgumentParser(description="Chexsa browser assistant")
    parser.add_argument("--resume", metavar="TASK_ID", help="Observe and reconcile a saved task; never replay its action log")
    parser.add_argument("--tasks", action="store_true", help="List recent local task IDs")
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=None, help="Task deadline in seconds")
    args = parser.parse_args(argv)
    if args.tasks:
        journal = TaskJournal()
        try:
            for task in journal.recent():
                print(f'{task["id"]}  {task["status"]}  {task["updated"]}')
        finally:
            journal.close()
        return
    if args.max_steps is not None and args.max_steps < 1 or args.timeout is not None and args.timeout < 1:
        parser.error("Step and time limits must be positive.")
    browser, agent = create_browser_agent(LLM(), max_steps=args.max_steps, timeout=args.timeout)
    try:
        if args.resume:
            result = agent.run_task(task_id=args.resume)
            print(f"Chexsa [{result.status}] > {result.message}")
            return
        print("Chexsa\nType 'exit' or 'quit' to close. Ctrl+C cancels a running task.\n")
        while True:
            try:
                request = input("You > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break
            if request.lower() in ("exit", "quit"):
                break
            if not request:
                continue
            response = agent.run(request)
            status = agent.last_result.status if agent.last_result else "failed"
            print(f"Chexsa [{status}] > {response}")
            if agent.state:
                print(f"[TASK] {agent.state.id}")
    finally:
        browser.close()


if __name__ == "__main__":
    main()
