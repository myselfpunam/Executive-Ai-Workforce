from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from control_sdk.cancellation import CancellationToken
from control_sdk.control_state import ControlState
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, Tracer

from .events import Event, new_id


@dataclass
class Step:
    """One atomic unit of work in a run. `action` is deterministic for the
    demo agent — it returns a plain dict, never calls a real model/API yet.

    accepts_cancellation_token=True means `action` takes one argument (the
    token) and may check it partway through its own work to stop early.
    False (the default) means `action` takes no arguments and always runs
    to completion once started — cancellation only takes effect at the next
    safe point, not mid-step. Both are correct; it depends on whether the
    underlying operation actually supports being interrupted.
    """

    name: str
    action: Callable[..., dict[str, Any]]
    step_id: str = field(default_factory=lambda: new_id("step"))
    accepts_cancellation_token: bool = False


@dataclass
class Run:
    run_id: str
    agent_name: str
    status: str = "RUNNING"
    events: list[Event] = field(default_factory=list)
    # Index of the step that hasn't started yet. This is the one number a
    # checkpoint needs to remember "where we stopped."
    next_step_index: int = 0

    def emit(self, type: str, step_id: str | None = None, data: dict[str, Any] | None = None) -> Event:
        event = Event.create(run_id=self.run_id, type=type, step_id=step_id, data=data)
        self.events.append(event)
        return event


class DemoAgent:
    """A deterministic agent: a fixed list of steps executed in order,
    controllable via the control-sdk package (ControlState, checkpointing).

    Alongside the plain Event log (used by our own tests and the future
    Control audit trail), every run now also emits real OpenTelemetry
    spans — one "agent.run" span per run, with one child "agent.step" span
    per step. The two are independent for now: Event stays what our tests
    assert on; spans are what Step 32's OTel Collector will consume.
    """

    def __init__(self, name: str, steps: list[Step], tracer: Tracer | None = None):
        self.name = name
        self.steps = steps
        self.tracer = tracer or trace.get_tracer("agent_runtime")

    def run(
        self,
        control_state: ControlState | None = None,
        resume: dict | None = None,
        checkpoint_path: str | None = None,
    ) -> Run:
        control_state = control_state or ControlState()

        if resume:
            # Continuing a run that was checkpointed earlier — same run_id,
            # pick up at the step index the checkpoint remembered.
            run = Run(run_id=resume["run_id"], agent_name=self.name, next_step_index=resume["next_step_index"])
            run.emit("run.resumed", data={"resumed_from_step_index": resume["next_step_index"]})
            start_index = resume["next_step_index"]
        else:
            run = Run(run_id=new_id("run"), agent_name=self.name)
            run.emit("run.started")
            start_index = 0

        with self.tracer.start_as_current_span(
            "agent.run",
            attributes={"run_id": run.run_id, "agent_name": self.name, "resumed": bool(resume)},
        ) as run_span:
            for index in range(start_index, len(self.steps)):
                step = self.steps[index]
                run.next_step_index = index

                # SAFE POINT: before step. PAUSE/STOP reject NEW work, so
                # this check must happen before a step is allowed to start.
                if self._check_safe_point(run, control_state):
                    self._maybe_checkpoint(run, control_state, checkpoint_path)
                    run_span.set_attribute("run.status", run.status)
                    return run

                with self.tracer.start_as_current_span(
                    "agent.step",
                    attributes={"step_name": step.name, "step_id": step.step_id},
                ) as step_span:
                    run.emit("step.started", step_id=step.step_id, data={"name": step.name})
                    try:
                        if step.accepts_cancellation_token:
                            result = step.action(CancellationToken(control_state))
                        else:
                            result = step.action()
                    except Exception as exc:
                        step_span.record_exception(exc)
                        step_span.set_status(Status(StatusCode.ERROR))
                        run.emit("step.failed", step_id=step.step_id, data={"error": str(exc)})
                        run.status = "FAILED"
                        run.emit("run.failed")
                        run_span.set_status(Status(StatusCode.ERROR))
                        run_span.set_attribute("run.status", run.status)
                        return run
                    run.emit("step.completed", step_id=step.step_id, data=result)
                    run.next_step_index = index + 1

                # SAFE POINT: after step. The step's own action may itself
                # have triggered a pause/stop request (e.g. an external
                # command arrived while the step was running) — catch that
                # here too, before starting the next step.
                if self._check_safe_point(run, control_state):
                    self._maybe_checkpoint(run, control_state, checkpoint_path)
                    run_span.set_attribute("run.status", run.status)
                    return run

            run.status = "COMPLETED"
            run.emit("run.completed")
            run_span.set_attribute("run.status", run.status)

        return run

    @staticmethod
    def _maybe_checkpoint(run: Run, control_state: ControlState, checkpoint_path: str | None) -> None:
        if checkpoint_path and run.status == "PAUSED":
            from control_sdk.checkpoint import save_checkpoint

            save_checkpoint(run.run_id, run.next_step_index, control_state, checkpoint_path)

    @staticmethod
    def _check_safe_point(run: Run, control_state: ControlState) -> bool:
        """Returns True if the run was halted (paused or cancelled) here."""
        if control_state.is_stop_requested():
            control_state.confirm_stopped()
            run.status = "CANCELLED"
            run.emit("run.cancelled")
            return True
        if control_state.is_pause_requested():
            control_state.confirm_paused()
            run.status = "PAUSED"
            run.emit("run.paused")
            return True
        return False
