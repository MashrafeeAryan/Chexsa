"""Defines the common LLM interface used by Chexsa.
Every model provider must return the same AgentDecision format.
This lets Chexsa switch models without changing the agent."""

from typing import Protocol

from agent import AgentDecision, StepResult
from browser_state import BrowserSnapshot


class LLMProvider(Protocol):
    """Describe the decision function every LLM provider must have."""

    def decide(
        self,
        request: str,
        state: BrowserSnapshot,
        history: list[StepResult],
    ) -> AgentDecision:
        """Choose the next action or actions for Chexsa."""
        ...
