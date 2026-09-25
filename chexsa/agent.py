"""Core agent controller for Chexsa."""


class Agent:
    """Receive user goals and coordinate Chexsa's capabilities."""

    def run(self, request: str) -> str:
        """Handle one user request and return a response."""
        # This method will later coordinate planning, tools, and verification.
        return f"Received: {request}"
