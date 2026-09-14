# control-api

**Plane:** Control (Command Truth).

**Role:** the only write endpoint for commands — `POST /control/v1/agents/{agent_id}/commands`. Owns policy/step-up, the append-only command ledger, the transactional outbox, the dispatcher (long-poll delivery to adapters), and reconciliation. Has no route to Twenty, model keys, or observation write APIs.

**Status:** Python/FastAPI. `POST /control/v1/agents/{agent_id}/commands` validates (reusing `control_sdk.command_schema`), checks+advances the agent's `expected_state_version` (409 on stale), then atomically writes the ledger + outbox rows — all one transaction. 13/13 tests passing. Still no auth/RBAC/step-up or tenant/department scope — anyone can currently issue a correctly-versioned command for any agent_id (deferred to Week 18). No dispatcher yet, so outbox rows just sit PENDING forever.

**Depends on:** `control-sdk-python/` and `control-sdk-ts/` existing, so there's an adapter contract to dispatch commands to. PostgreSQL for the ledger/outbox (own database — never shared with Observation; see `.env.example`).

**Local Postgres setup (already done on this machine):**
```sql
CREATE ROLE executive_control_app WITH LOGIN PASSWORD '...';
CREATE DATABASE executive_control_dev OWNER executive_control_app;
```
Copy `.env.example` to `.env` and fill in the real local password.
