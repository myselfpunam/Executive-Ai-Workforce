# control-api

**Plane:** Control (Command Truth).

**Role:** the only write endpoint for commands — `POST /control/v1/agents/{agent_id}/commands`. Owns policy/step-up, the append-only command ledger, the transactional outbox, the dispatcher (long-poll delivery to adapters), and reconciliation. Has no route to Twenty, model keys, or observation write APIs.

**Status:** not started — Week 8-12 of the roadmap.

**Depends on:** `control-sdk-python/` and `control-sdk-ts/` existing, so there's an adapter contract to dispatch commands to. PostgreSQL for the ledger/outbox (own database — never shared with Observation).
