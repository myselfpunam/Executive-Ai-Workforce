-- Own database entirely (executive_observation_dev) — never shared with
-- the Control Plane's executive_control_dev (CLAUDE.md section 5).
-- Append-only, same principle as command_ledger, PLUS a hash chain for
-- tamper-evidence (see observation_plane/event_store.py).

CREATE TABLE observation_events (
    event_id        BIGSERIAL PRIMARY KEY,
    trace_id        TEXT NOT NULL,
    span_id         TEXT NOT NULL,
    parent_span_id  TEXT,
    name            TEXT NOT NULL,
    start_time      TEXT NOT NULL,
    end_time        TEXT NOT NULL,
    status          TEXT NOT NULL,
    attributes      JSONB NOT NULL DEFAULT '{}'::jsonb,
    previous_hash   TEXT NOT NULL,
    evidence_hash   TEXT NOT NULL,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_observation_events_trace_id ON observation_events (trace_id);

CREATE OR REPLACE FUNCTION reject_observation_mutation() RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'observation_events is append-only: % is not allowed', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER observation_events_no_update
    BEFORE UPDATE ON observation_events
    FOR EACH ROW EXECUTE FUNCTION reject_observation_mutation();

CREATE TRIGGER observation_events_no_delete
    BEFORE DELETE ON observation_events
    FOR EACH ROW EXECUTE FUNCTION reject_observation_mutation();
