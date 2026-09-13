from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .control_state import ControlState
from .events import Event, new_id


@dataclass
class Step:
    """One atomic unit of work in a run. `action` is deterministic for the
    demo agent — it returns a plain dict, never calls a real model/API yet.
    """

    name: str
    action: Callable[[], dict[str, Any]]
    step_id: str = field(default_factory=lambda: new_id("step"))


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
    """A deterministic agent: a fixed list of steps executed in order.

    Safe points are marked with comments, not enforced — the Control SDK
    (Week 5-7) is what will turn these into real pause/stop checks.
    """

    def __init__(self, name: str, steps: list[Step]):
        self.name = name
        self.steps = steps

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

        for index in range(start_index, len(self.steps)):
            step = self.steps[index]
            run.next_step_index = index

            # SAFE POINT: before step. PAUSE/STOP reject NEW work, so this
            # check must happen before a step is allowed to start.
            if self._check_safe_point(run, control_state):
                self._maybe_checkpoint(run, control_state, checkpoint_path)
                return run

            run.emit("step.started", step_id=step.step_id, data={"name": step.name})
            try:
                result = step.action()
            except Exception as exc:
                run.emit("step.failed", step_id=step.step_id, data={"error": str(exc)})
                run.status = "FAILED"
                run.emit("run.failed")
                return run
            run.emit("step.completed", step_id=step.step_id, data=result)
            run.next_step_index = index + 1

            # SAFE POINT: after step. The step's own action may itself have
            # triggered a pause/stop request (e.g. an external command
            # arrived while the step was running) — catch that here too,
            # before starting the next step.
            if self._check_safe_point(run, control_state):
                self._maybe_checkpoint(run, control_state, checkpoint_path)
                return run

        run.status = "COMPLETED"
        run.emit("run.completed")
        return run

    @staticmethod
    def _maybe_checkpoint(run: Run, control_state: ControlState, checkpoint_path: str | None) -> None:
        if checkpoint_path and run.status == "PAUSED":
            from .checkpoint import save_checkpoint  # local import: avoids a circular import at module load time

            save_checkpoint(run, control_state, checkpoint_path)

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
