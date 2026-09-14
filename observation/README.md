# observation

**Plane:** Observation (Execution Truth), read-only.

**Role:** OTel Collector ingest → Privacy Gate (allowlist/redact/normalize) → append-only Event Store with evidence hashes → Projection + Observation API (status, cost, coverage, SSE). Has no route to any command endpoint.

**Status:** OTel Collector running locally (`collector/`, real `otelcol` v0.160.0 binary — not Docker, since this machine doesn't have it), OTLP receiver on :4317 (gRPC) / :4318 (HTTP), currently exporting to console (`debug` exporter). `agent-runtime` can send real spans to it (proven). Privacy Gate (allowlist + redact + normalize), Event Store (own database, append-only + hash-chained), Projection engine (per-run summaries), and Observation API (`GET /observation/v1/runs/{trace_id}` snapshot + `GET /observation/v1/events/stream` resumable SSE) are all built and tested. **Not yet wired end-to-end** — nothing currently pulls spans out of the OTel Collector and pushes them through the Privacy Gate into the Event Store automatically; each piece is proven independently but there's no live pipeline connecting Collector -> Privacy Gate -> Event Store yet. That wiring is the natural next increment whenever this plane needs to go live for real.

**Run it:** `./collector/start.sh` (foreground; Ctrl+C to stop). The binary itself is gitignored — see that script for how to re-fetch it.

**Depends on:** `agent-runtime/` emitting telemetry (done, Step 31). Own PostgreSQL/object-store database — never shared with `control-api/`.
