"""Core agent controller for Chexsa."""


class Agent:
    """Connect the user request, browser state, LLM, and Playwright."""

    def __init__(
        self,
        browser_state=None,
        llm=None,
        playwright=None,
        max_steps: int = 20,
    ) -> None:
        self.browser_state = browser_state
        self.llm = llm
        self.playwright = playwright
        self.max_steps = max_steps

    def run(self, request: str) -> str:
        """Run the browser agent until the LLM says the task is finished."""
        if not all((self.browser_state, self.llm, self.playwright)):
            return "Agent controller is ready, but browser tools are not connected yet."

        for _ in range(self.max_steps):
            # 1. Get the current browser state: URL + ARIA + DOM.
            state = self.browser_state.get_state()

            # 2. Give the user request and browser state to the LLM.
            decision = self.llm.decide(
                request=request,
                url=state["url"],
                aria=state["aria"],
                dom=state["dom"],
            )

            # 3. Stop when the LLM says the task is complete.
            if decision["action"] == "done":
                return decision.get("response", "Task complete.")

            # 4. Send the LLM's action to Playwright.
            self.playwright.execute(
                action=decision["action"],
                arguments=decision.get("arguments", {}),
            )

            # 5. Loop again and fetch the new browser state.

        return "Stopped because the maximum number of steps was reached."
