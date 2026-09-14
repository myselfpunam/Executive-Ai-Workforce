# observation

**Plane:** Observation (Execution Truth), read-only.

**Role:** OTel Collector ingest → Privacy Gate (allowlist/redact/normalize) → append-only Event Store with evidence hashes → Projection + Observation API (status, cost, coverage, SSE). Has no route to any command endpoint.

**Status:** OTel Collector running locally (`collector/`, real `otelcol` v0.160.0 binary — not Docker, since this machine doesn't have it), OTLP receiver on :4317 (gRPC) / :4318 (HTTP), currently exporting to console (`debug` exporter). `agent-runtime` can send real spans to it (proven). Fully wired end-to-end: `agent-runtime`'s OTel spans -> `ObservationStoreExporter` (an OTel SDK exporter, `ingest_exporter.py`) -> Privacy Gate -> Event Store -> Projection -> Observation API (`GET /observation/v1/runs`, `GET /observation/v1/runs/{trace_id}`, `GET /observation/v1/events/stream`). Scoping note: this ingests directly at the OTel SDK level, not by parsing the standalone Collector's OTLP wire output (real OTLP JSON/protobuf parsing is a bigger, separate task) — the Collector (Step 32) remains real and useful for feeding other external tools independently. Known cleanup item: dev/test share one database, so old test runs show up as noise in real queries.

**Run it:** `./collector/start.sh` (foreground; Ctrl+C to stop). The binary itself is gitignored — see that script for how to re-fetch it.

**Depends on:** `agent-runtime/` emitting telemetry (done, Step 31). Own PostgreSQL/object-store database — never shared with `control-api/`.
