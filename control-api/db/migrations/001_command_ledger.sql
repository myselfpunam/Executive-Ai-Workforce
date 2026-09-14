-- CLAUDE.md section 13: "append-only command ledger". Every command
-- lifecycle transition (CLAUDE.md section 10) is a new row here, never an
-- edit to an old one. A correction is a new event, not a rewritten fact.

CREATE TABLE command_ledger (
    ledger_id               BIGSERIAL PRIMARY KEY,
    command_id              TEXT NOT NULL,
    event_type              TEXT NOT NULL CHECK (event_type IN (
                                 'REQUESTED', 'AUTHORIZED', 'QUEUED', 'DELIVERED',
                                 'ACKED', 'APPLIED', 'REJECTED', 'EXPIRED',
                                 'FAILED', 'UNSUPPORTED'
                             )),
    agent_id                TEXT NOT NULL,
    action                  TEXT NOT NULL CHECK (action IN ('PAUSE', 'STOP', 'RESUME')),
    expected_state_version  INTEGER NOT NULL,
    reason                  TEXT NOT NULL,
    -- Everything from the canonical control contract (CLAUDE.md section 8)
    -- that doesn't have its own column yet — actor, delivery, integrity
    -- fields. Structured columns can be split out later if we need to
    -- query them directly; JSONB is fine for "store it faithfully" now.
    detail                  JSONB NOT NULL DEFAULT '{}'::jsonb,
    recorded_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_command_ledger_command_id ON command_ledger (command_id);
CREATE INDEX idx_command_ledger_agent_id ON command_ledger (agent_id);

-- Enforce append-only at the database level — never trust application code
-- alone to "just not" issue an UPDATE or DELETE.
CREATE OR REPLACE FUNCTION reject_ledger_mutation() RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'command_ledger is append-only: % is not allowed', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER command_ledger_no_update
    BEFORE UPDATE ON command_ledger
    FOR EACH ROW EXECUTE FUNCTION reject_ledger_mutation();

CREATE TRIGGER command_ledger_no_delete
    BEFORE DELETE ON command_ledger
    FOR EACH ROW EXECUTE FUNCTION reject_ledger_mutation();
