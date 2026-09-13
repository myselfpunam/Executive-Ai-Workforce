# control-sdk-python

**Plane:** Control (agent-side adapter).

**Role:** the small library a Python agent runtime embeds to become controllable — safe checkpoints, cooperative cancellation, heartbeat, capability advertisement, idempotent command inbox. This is what `agent-runtime/` will install once it exists.

**Status:** not started — Week 5-7 of the roadmap.

**Depends on:** `agent-runtime/` existing first, so there's something real to make controllable.
