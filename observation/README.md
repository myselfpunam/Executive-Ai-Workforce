# observation

**Plane:** Observation (Execution Truth), read-only.

**Role:** OTel Collector ingest → Privacy Gate (allowlist/redact/normalize) → append-only Event Store with evidence hashes → Projection + Observation API (status, cost, coverage, SSE). Has no route to any command endpoint.

**Status:** not started — Week 13-14 of the roadmap.

**Depends on:** `agent-runtime/` emitting telemetry. Own PostgreSQL/object-store database — never shared with `control-api/`.
