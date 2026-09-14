# control-sdk-python

**Plane:** Control (agent-side adapter).

**Role:** the small library a Python agent runtime embeds to become controllable — safe checkpoints, cooperative cancellation, heartbeat, capability advertisement, idempotent command inbox. This is what `agent-runtime/` will install once it exists.

**Status:** core pieces implemented and tested (state machine, safe-point enforcement contract, checkpoint save/load, heartbeat freshness, capability advertisement, idempotent command inbox) — 16/16 tests passing. Not yet wired to any real network/adapter transport.

**Depends on:** nothing — this package is intentionally standalone. `agent-runtime/` depends on it, not the other way around.

**Install (local dev):** `pip install -e ./control-sdk-python[dev]` into the shared repo-root venv, before installing `agent-runtime`.
