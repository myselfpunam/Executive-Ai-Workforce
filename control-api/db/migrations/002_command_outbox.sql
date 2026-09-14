-- Unlike command_ledger, this table IS a working queue, not permanent
-- history — rows get marked DISPATCHED (an update is fine here) and could
-- even be cleaned up later. It answers "what still needs to be sent?",
-- while command_ledger answers "what happened, ever?".

CREATE TABLE command_outbox (
    outbox_id               BIGSERIAL PRIMARY KEY,
    command_id              TEXT NOT NULL UNIQUE,
    agent_id                TEXT NOT NULL,
    action                  TEXT NOT NULL CHECK (action IN ('PAUSE', 'STOP', 'RESUME')),
    expected_state_version  INTEGER NOT NULL,
    reason                  TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'DISPATCHED')),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    dispatched_at           TIMESTAMPTZ
);

-- The Dispatcher (Step 25) will poll exactly this: oldest pending first.
CREATE INDEX idx_command_outbox_pending ON command_outbox (created_at) WHERE status = 'PENDING';
