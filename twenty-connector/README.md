# twenty-connector

**Plane:** Twenty CRM (Business Truth), read-only.

**Role:** scoped read-only API access to Twenty, signed webhook handling for fast create/update/delete signals, and a reconciliation poller for anything the webhook missed. Never transports control commands; never becomes a shared database with the Control Plane.

**Status:** complete for V1 scope. Self-hosted Twenty CRM running locally via Docker. Read-only `TwentyClient` (only list_companies/list_people/list_opportunities, no write methods — enforced structurally). Signed webhook receiver (`app.py`, HMAC-SHA256 per Twenty's own spec, timing-safe comparison, stale-timestamp rejection) — built and tested at the code level, not yet registered with the live Twenty instance's webhook settings. Cursor-based reconciliation poller (`reconciliation.py`) proven against the real instance. 16/16 tests passing.

**Run it:** `cd self-hosted && docker compose up -d` (already running). First visit http://localhost:3000 to create the initial workspace/account — required before an API key can be generated for the connector.

**Depends on:** a running, self-hosted Twenty CRM instance to connect to (done).
