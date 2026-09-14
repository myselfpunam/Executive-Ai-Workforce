from __future__ import annotations

from dataclasses import dataclass

# CLAUDE.md section 11: request body must contain EXACTLY these three
# fields. No prompt, tool, URL, model, schedule, target-data, script, or
# generic-payload field is ever permitted — this is the whole point of the
# Control Plane staying a closed three-action system.
VALID_ACTIONS = {"PAUSE", "STOP", "RESUME"}
REQUIRED_FIELDS = {"action", "expected_state_version", "reason"}
ALLOWED_FIELDS = REQUIRED_FIELDS

# CLAUDE.md section 10: full command lifecycle. Not enforced here yet
# (that's the Control API's job, Step 21+) — frozen now so every future
# piece uses the same vocabulary instead of inventing its own strings.
LIFECYCLE_STATUSES = {
    "REQUESTED",
    "AUTHORIZED",
    "QUEUED",
    "DELIVERED",
    "ACKED",
    "APPLIED",
    "REJECTED",
    "EXPIRED",
    "FAILED",
    "UNSUPPORTED",
}


@dataclass(frozen=True)
class ValidationError:
    code: str
    message: str


def validate_command_request(raw: dict) -> ValidationError | None:
    """Returns None if `raw` matches the canonical command contract
    exactly, otherwise a ValidationError describing what's wrong. Never
    tries to "fix" or coerce a bad request — reject it and say why."""
    extra_fields = set(raw.keys()) - ALLOWED_FIELDS
    if extra_fields:
        return ValidationError("SCHEMA_VALIDATION_FAILED", f"unexpected field(s): {sorted(extra_fields)}")

    missing_fields = REQUIRED_FIELDS - set(raw.keys())
    if missing_fields:
        return ValidationError("SCHEMA_VALIDATION_FAILED", f"missing field(s): {sorted(missing_fields)}")

    if raw["action"] not in VALID_ACTIONS:
        return ValidationError("UNKNOWN_ACTION", f"action must be one of {sorted(VALID_ACTIONS)}")

    version = raw["expected_state_version"]
    if not isinstance(version, int) or isinstance(version, bool) or version < 0:
        return ValidationError("SCHEMA_VALIDATION_FAILED", "expected_state_version must be a non-negative integer")

    reason = raw["reason"]
    if not isinstance(reason, str) or not reason.strip():
        return ValidationError("SCHEMA_VALIDATION_FAILED", "reason must be a non-empty string")

    return None
