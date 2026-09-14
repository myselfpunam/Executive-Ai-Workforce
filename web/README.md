# web

**Plane:** Executive Experience — the one screen that joins both trust boundaries (Observation + Control), plus a view-only Twenty widget.

**Role:** the BFF (separate clients for the Observation API and the Control API) and the standalone executive dashboard — agent/run/step views, CRM context, the three command buttons, and command proof/status UI. Must never claim a command is Applied before runtime proof arrives.

**Status:** first real dashboard live. BFF (`src/bff.ts`, zero runtime deps) proxies `/bff/runs`, `/bff/runs/:traceId`, `/bff/agents/:agentId/commands` and serves `public/index.html` — a plain HTML/JS run-overview table (no framework yet; add one only if the UI outgrows this), polling `/bff/runs` every 5s. 7/7 tests passing. Run with `npm start` (reads `CONTROL_API_URL`/`OBSERVATION_API_URL`/`PORT` env vars). No command buttons, run replay, CRM panel, or auth yet.

**Depends on:** `observation/` and `control-api/` both existing (done).
