"""Controls Chexsa's main observe, decide, and act loop.
Verification is optional for now and can be added later."""

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
    verified: bool | None = None
    error: str | None = None


ObserveFn = Callable[[], Any]
DecideFn = Callable[[str, Any, list[StepResult]], AgentDecision]
ExecuteFn = Callable[[str, dict[str, Any]], Any]
VerifyFn = Callable[[str, dict[str, Any], Any], bool]


class Agent:
    """Run Chexsa's observe, decide, and act loop."""

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
        """Keep working until the task finishes or reaches the step limit."""

        if not self._is_configured():
            return "Agent controller is ready, but its tools are not connected yet."

        history: list[StepResult] = []

        # Start each step by reading the latest state.
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
        """Run one action and save what happened."""

        try:
            result = self.execute(decision.action, decision.arguments)

            # Only verify the action when a verifier has been connected.
            verified = None
            if self.verify is not None:
                verified = self.verify(
                    decision.action,
                    decision.arguments,
                    result,
                )

            return StepResult(
                action=decision.action,
                arguments=decision.arguments,
                result=result,
                verified=verified,
            )

        except Exception as error:
            # Save failures so the LLM can react on the next step.
            return StepResult(
                action=decision.action,
                arguments=decision.arguments,
                error=str(error),
            )

    def _is_configured(self) -> bool:
        """Check that the required parts of the agent are connected."""

        return all((self.observe, self.decide, self.execute))
