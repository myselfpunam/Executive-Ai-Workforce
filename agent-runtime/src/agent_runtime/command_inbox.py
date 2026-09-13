from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class CommandResult:
    command_id: str
    status: str
    resulting_state: str
    state_version: int


class CommandInbox:
    """Delivery is at-least-once (CLAUDE.md section 10) — the same command
    can legitimately arrive twice (a retry after a slow/lost ack). This
    remembers every command's result by its immutable command_id, so a
    repeat delivery gets back the SAME result instead of being applied
    again — one effect, one audit trail, per CLAUDE.md section 14."""

    def __init__(self) -> None:
        self._results: dict[str, CommandResult] = {}

    def handle(self, command_id: str, apply: Callable[[], CommandResult]) -> CommandResult:
        if command_id in self._results:
            return self._results[command_id]
        result = apply()
        self._results[command_id] = result
        return result
