# IMPLEMENTATION_STEPS.md

A flat, sequential build list — no week numbers. Check WEEKLY_ROADMAP.md if you want the week/hour framing; this file is for "where exactly are we in the build" at a glance. Update the checkbox only when CHECKLIST.md's completion rule is actually met (works + tested + understood), not just when code exists.

## Phase 1 — Core Control Room

- [x] 1. GitHub repo + local dev environment (Python venv, Node, checked for Docker)
- [x] 2. Project documentation (CLAUDE.md, PROJECT_CONTEXT.md, WEEKLY_ROADMAP.md, CHECKLIST.md, LEARNING_RULES.md, START_HERE.md)
- [x] 3. Repo folder structure, one folder per architectural plane
- [x] 4. Structured `Event` definition (`agent-runtime/events.py`)
- [x] 5. `Run` + `Step` + execution loop (`agent-runtime/loop.py`)
- [x] 6. Deterministic demo agent (`agent-runtime/demo.py`)
- [x] 7. Tests for the execution loop — 3/3 passing
- [x] 8. Control state machine (ACTIVE / PAUSED / STOPPED / UNKNOWN) — 6/6 tests passing
- [x] 9. Wire real safe-point checks into the loop — 13/13 tests passing, a running demo agent genuinely stops at PAUSE/STOP
- [x] 10. Checkpoint persistence — 15/15 tests passing, a full pause → simulated restart → resume cycle proven, no redone work
- [x] 11. Heartbeat mechanism — 18/18 tests passing, stale/missing heartbeat correctly reports UNKNOWN, never guesses
- [x] 12. Capability advertisement — 22/22 tests passing; unsupported actions and stale heartbeats both correctly block a control
- [x] 13. Idempotent command inbox — 24/24 tests passing, a duplicate command_id never double-applies
- [x] 14. Packaged 8–13 into `control-sdk-python/` as a standalone library — `agent-runtime` now imports it, not the reverse (16/16 + 9/9 tests passing)
- [x] 15. Cancellation token support for cooperative STOP — 29/29 tests passing; proven a token-aware step bails out early instead of wasting work
- [x] 16. Ported the full SDK contract to `control-sdk-ts/` — 18/18 tests passing, matching control-sdk-python's 18 exactly
- [x] 17. Froze the command schema + error codes in both SDKs — 61/61 tests passing total; a smuggled "prompt" field is rejected before it ever reaches an agent
- [x] 18. PostgreSQL running locally — dedicated `executive_control_app` role + `executive_control_dev` database, connection verified, isolated from Observation's future database
- [x] 19. Command ledger table (append-only) — table + database-level UPDATE/DELETE-rejecting triggers, proven live against the real Postgres database (not just tested in application code)
- [x] 20. Transactional outbox table + pattern — proven live: a failure partway through the shared transaction rolls back BOTH the ledger and outbox writes, no partial state (2/2 tests passing). control-api built in Python.
- [x] 21. Control API skeleton — `POST /control/v1/agents/{agent_id}/commands` live (FastAPI), reuses the SDK's validator as the single source of truth, proven end-to-end into the real database (7/7 tests passing)
- [x] 22. Policy engine — expected_state_version optimistic-concurrency check live and proven (stale version correctly rejected with 409); tenant/department scope deliberately deferred to Week 18 (needs real auth first). 74/74 tests passing across all packages.
- [x] 23. Step-up check for STOP — placeholder token required only for STOP, PAUSE/RESUME unaffected (18/18 control-api tests passing). Real MFA still deferred to Week 18.
- [x] 24. Wire Control API to ledger+outbox in one DB transaction — done as part of Step 20/22 (submit_command_transaction already does this)
- [x] 25. Dispatcher process — claims the oldest PENDING command per agent using FOR UPDATE SKIP LOCKED, proven with real concurrent threads (5 simultaneous claim attempts, exactly 1 succeeds, 24/24 control-api tests passing)
- [x] 26. Long-poll delivery endpoint — `GET /control/v1/agents/{agent_id}/commands/poll`, proven to genuinely wait and catch a command that arrives mid-wait (29/29 tests passing); ledger now shows REQUESTED -> DELIVERED in order
- [x] 27. Acknowledgement handling — full lifecycle REQUESTED->DELIVERED->APPLIED/FAILED/etc. proven, idempotent duplicate acks, and a FAILED ack correctly corrects the optimistic state_version back to reality (34/34 tests passing)
- [x] 28. Reconciliation job — stale DELIVERED commands past a TTL are marked EXPIRED (not guessed APPLIED), idempotent across repeated runs (38/38 tests passing). Heartbeat-based reconciliation deferred until agents can heartbeat into the Control API.
- [x] 29. Duplicate-delivery test (same command_id twice → one effect, proven) — already covered: dispatcher concurrency test (Step 25) + idempotent ack test (Step 27)
- [x] 30. Restart/recovery test — proven end-to-end using fresh, independent connections at every phase (nothing depends on Python process memory surviving); 40/40 control-api tests passing. **Week 11-12 (Dispatcher/Long-poll/Ack/Reconciliation) complete.**
- [x] 31. Real OpenTelemetry instrumentation in agent-runtime — one `agent.run` span per run with a child `agent.step` span per step, correct trace_id/parent linkage and error status proven (16/16 agent-runtime tests, 106/106 total). Event log kept alongside spans, not replaced.
- [x] 32. OTel Collector running locally — real `otelcol` binary (no Docker on this machine), OTLP gRPC+HTTP receiver live; agent-runtime spans proven to arrive over the network with correct trace/parent linkage and attributes
- [x] 33. Privacy Gate — allowlist (unknown fields dropped entirely) + redaction (email/API-key/card-number patterns scrubbed inside allowed fields) + normalization into `ObservationEvent`, 7/7 tests passing
- [x] 34. Event Store — own database (executive_observation_dev), append-only + trigger-enforced, hash-chained evidence proven to catch tampering even when the trigger itself is bypassed by a superuser (11/11 observation tests passing)
- [x] 35. Projection engine — raw events folded into a per-run summary (status, step count, duration); cost/coverage honestly omitted, no real data source yet. Fixed a real bug along the way: an earlier tamper test was permanently corrupting the shared dev DB by committing instead of rolling back. 121/121 tests passing across all 5 packages.
- [x] 36. Observation API — `GET /observation/v1/runs/{trace_id}` snapshot + `GET /observation/v1/events/stream` resumable SSE (Last-Event-ID honored, no gaps/repeats proven). Along the way, found and fixed a real psycopg3 footgun: an un-transacted read before a write left a dangling transaction invisible to other connections — fixed via autocommit=True on test connections (both observation and control-api). 129/129 tests passing across all 5 packages. **Week 13-14 (Observation Plane) complete.**
- [x] 37. Self-hosted Twenty CRM instance running — official docker-compose (server/worker/db/redis), Docker Desktop installed along the way (needed a manual sudo step from the user), health check passing at http://localhost:3000
- [x] 38. Twenty read-only connector — TwentyClient with only list_companies/list_people/list_opportunities, tested against the real running instance (4/4 tests passing, including a structural test that fails if a write method is ever added)
- [x] 39. Twenty signed webhook receiver — HMAC-SHA256 verification (per Twenty's own spec), timing-safe comparison, stale-timestamp rejection, tampered-body rejection all proven (12/12 tests passing). Not yet registered with the real running Twenty instance — code-level proof only so far.
- [ ] 40. Twenty reconciliation poller (catches anything the webhook missed) ← **next**
- [ ] 41. BFF joining Observation API + Control API
- [ ] 42. Executive dashboard — agent/run overview
- [ ] 43. Run replay / timeline view
- [ ] 44. CRM context panel (Twenty widget, view-only, deep link)
- [ ] 45. Command controls UI — the three buttons, wired to the real Control API
- [ ] 46. Command proof/status UI (Requested → ... → Applied, shown honestly)
- [ ] 47. OIDC login for the dashboard
- [ ] 48. MFA / step-up flow for STOP, in the real UI
- [ ] 49. Department-based RBAC enforced end to end
- [ ] 50. PostgreSQL Row-Level Security (RLS) policies
- [ ] 51. CSRF protection on the BFF
- [ ] 52. Failure/chaos test pass: adapter offline, stale state-version, forged command, network partition, disk pressure
- [ ] 53. Security test pass: cross-role and cross-department access correctly denied
- [ ] 54. **Phase 1 complete** — full integration demo, deployment, documentation

## Phase 2 — Vendor Distribution Plane

- [ ] 55. Private source + CI pipeline for building the product itself
- [ ] 56. Build signing with KMS/HSM + provenance
- [ ] 57. SBOM generation per build
- [ ] 58. Artifact registry (signed OCI artifacts)
- [ ] 59. Licence Service (vendor side) — issues signed, per-customer scoped entitlements
- [ ] 60. Local Licence Verifier (customer side) — verify + cached lease, works offline
- [ ] 61. Update Service (vendor side) — signed release metadata
- [ ] 62. Local Update Verifier (customer side) — signature check + human admin approval
- [ ] 63. Vendor Admin Portal (OIDC/MFA/audit) for managing customers and releases
- [ ] 64. Network isolation proof — automated check that no telemetry export or reverse control path exists
- [ ] 65. **Project complete** — full Phase 1 + Phase 2 integration, final docs, deployment guide, final demo
