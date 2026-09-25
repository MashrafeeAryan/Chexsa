"""Core agent controller for Chexsa."""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class AgentDecision:
    """Describe what the LLM wants Chexsa to do next."""

    action: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    done: bool = False
    response: str = ""


@dataclass
class StepResult:
    """Store what happened after one attempted action."""

    action: str
    arguments: dict[str, Any]
    result: Any = None
    verified: bool = False
    error: str | None = None


ObserveFn = Callable[[], Any]
DecideFn = Callable[[str, Any, list[StepResult]], AgentDecision]
ExecuteFn = Callable[[str, dict[str, Any]], Any]
VerifyFn = Callable[[str, dict[str, Any], Any], bool]


class Agent:
    """Run Chexsa's observe, decide, act, and verify loop."""

    def __init__(
        self,
        observe: ObserveFn | None = None,
        decide: DecideFn | None = None,
        execute: ExecuteFn | None = None,
        verify: VerifyFn | None = None,
        max_steps: int = 20,
    ) -> None:
        self.observe = observe
        self.decide = decide
        self.execute = execute
        self.verify = verify
        self.max_steps = max_steps

    def run(self, request: str) -> str:
        """Keep working on a request until it finishes or reaches a safe stop."""
        if not self._is_configured():
            return "Agent controller is ready, but browser tools are not connected yet."

        history: list[StepResult] = []

        # Each loop starts from fresh state so Chexsa reacts to what actually happened.
        for _ in range(self.max_steps):
            state = self.observe()
            decision = self.decide(request, state, history)

            if decision.done:
                return decision.response or "Task complete."

            if not decision.action:
                return "Chexsa could not choose a next action."

            step = self._run_step(decision)
            history.append(step)

        return f"Stopped after {self.max_steps} steps before the task was complete."

    def _run_step(self, decision: AgentDecision) -> StepResult:
        """Execute one action and record whether it worked."""
        try:
            result = self.execute(decision.action, decision.arguments)
            verified = self.verify(decision.action, decision.arguments, result)
            return StepResult(
                action=decision.action,
                arguments=decision.arguments,
                result=result,
                verified=verified,
            )
        except Exception as error:
            # Tool failures become task history so the next LLM step can recover.
            return StepResult(
                action=decision.action,
                arguments=decision.arguments,
                error=str(error),
            )

    def _is_configured(self) -> bool:
        """Check that every part of the control loop has been connected."""
        return all((self.observe, self.decide, self.execute, self.verify))
