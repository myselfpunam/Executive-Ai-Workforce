// Same contract as control-sdk-python/src/control_sdk/command_schema.py

// CLAUDE.md section 11: request body must contain EXACTLY these three
// fields. No prompt, tool, URL, model, schedule, target-data, script, or
// generic-payload field is ever permitted.
export const VALID_ACTIONS = new Set(["PAUSE", "STOP", "RESUME"]);
export const REQUIRED_FIELDS = new Set(["action", "expected_state_version", "reason"]);
const ALLOWED_FIELDS = REQUIRED_FIELDS;

// CLAUDE.md section 10: full command lifecycle. Not enforced here yet
// (that's the Control API's job) — frozen now so every future piece uses
// the same vocabulary instead of inventing its own strings.
export const LIFECYCLE_STATUSES = new Set([
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
]);

export interface ValidationError {
  code: string;
  message: string;
}

/** Returns null if `raw` matches the canonical command contract exactly,
 * otherwise a ValidationError describing what's wrong. Never tries to
 * "fix" or coerce a bad request — reject it and say why. */
export function validateCommandRequest(raw: Record<string, unknown>): ValidationError | null {
  const keys = Object.keys(raw);
  const extraFields = keys.filter((k) => !ALLOWED_FIELDS.has(k));
  if (extraFields.length > 0) {
    return { code: "SCHEMA_VALIDATION_FAILED", message: `unexpected field(s): ${extraFields.sort().join(", ")}` };
  }

  const missingFields = [...REQUIRED_FIELDS].filter((f) => !(f in raw));
  if (missingFields.length > 0) {
    return { code: "SCHEMA_VALIDATION_FAILED", message: `missing field(s): ${missingFields.sort().join(", ")}` };
  }

  const action = raw.action;
  if (typeof action !== "string" || !VALID_ACTIONS.has(action)) {
    return { code: "UNKNOWN_ACTION", message: `action must be one of ${[...VALID_ACTIONS].sort().join(", ")}` };
  }

  const version = raw.expected_state_version;
  if (typeof version !== "number" || !Number.isInteger(version) || version < 0) {
    return { code: "SCHEMA_VALIDATION_FAILED", message: "expected_state_version must be a non-negative integer" };
  }

  const reason = raw.reason;
  if (typeof reason !== "string" || reason.trim() === "") {
    return { code: "SCHEMA_VALIDATION_FAILED", message: "reason must be a non-empty string" };
  }

  return null;
}
