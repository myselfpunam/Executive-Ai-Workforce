# twenty-connector

**Plane:** Twenty CRM (Business Truth), read-only.

**Role:** scoped read-only API access to Twenty, signed webhook handling for fast create/update/delete signals, and a reconciliation poller for anything the webhook missed. Never transports control commands; never becomes a shared database with the Control Plane.

**Status:** self-hosted Twenty CRM running locally via Docker (`self-hosted/docker-compose.yml`, official upstream config) — server + worker + its own Postgres + Redis, health check passing at http://localhost:3000. Read-only `TwentyClient` (`src/twenty_connector/client.py`) built and tested against the real instance — only list_companies/list_people/list_opportunities exist, no write methods (enforced structurally, not just by convention). No webhook receiver or reconciliation poller yet.

**Run it:** `cd self-hosted && docker compose up -d` (already running). First visit http://localhost:3000 to create the initial workspace/account — required before an API key can be generated for the connector.

**Depends on:** a running, self-hosted Twenty CRM instance to connect to (done).
