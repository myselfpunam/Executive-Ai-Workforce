# agent-runtime

**Plane:** AI / Business Plane (the "existing AI and business plane" the blueprint says stays authoritative).

**Role:** the demo AI agent — trigger → agent loop with checkpoint hooks + cancel token → model/tools → business action. This is what the Control Plane will eventually pause/stop/resume, and what the Observation Plane will watch via one-way telemetry.

**Status:** in progress — deterministic demo agent + execution loop done, now controllable via `control-sdk-python` (pause/stop/checkpoint all proven with tests).

**Depends on:** `control-sdk-python` (install it first: `pip install -e ./control-sdk-python[dev]`, then `pip install -e ./agent-runtime[dev]`).
