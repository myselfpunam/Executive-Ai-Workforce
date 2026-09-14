# web

**Plane:** Executive Experience — the one screen that joins both trust boundaries (Observation + Control), plus a view-only Twenty widget.

**Role:** the BFF (separate clients for the Observation API and the Control API) and the standalone executive dashboard — agent/run/step views, CRM context, the three command buttons, and command proof/status UI. Must never claim a command is Applied before runtime proof arrives.

**Status:** BFF built (`src/bff.ts`, TypeScript/Node, zero runtime deps) — proxies `GET /bff/runs/:traceId` to the Observation API and `POST /bff/agents/:agentId/commands` to the Control API, 5/5 tests passing. No frontend/dashboard UI yet.

**Depends on:** `observation/` and `control-api/` both existing (done).
