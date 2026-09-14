-- Tracks state_version as LAST ACCEPTED BY THE CONTROL API — not yet
-- confirmed-applied by the real agent runtime. Reconciliation (a later
-- step, once the dispatcher/heartbeat pipeline exists) is what corrects
-- this if the real agent disagrees. Good enough now to catch the common
-- "stale browser tab" / "double-click Pause" cases.

CREATE TABLE agent_state (
    agent_id      TEXT PRIMARY KEY,
    state_version INTEGER NOT NULL DEFAULT 0,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
