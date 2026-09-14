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
- [ ] 23. Step-up check for STOP (basic version, before full MFA) ← **next**
- [ ] 24. Wire Control API to ledger+outbox in one DB transaction
- [ ] 25. Dispatcher process (reads outbox, delivers toward the adapter)
- [ ] 26. Long-poll delivery endpoint (adapter pulls commands)
- [ ] 27. Acknowledgement handling (adapter reports result back)
- [ ] 28. Reconciliation job (command state vs. fresh adapter heartbeat)
- [ ] 29. Duplicate-delivery test (same command_id twice → one effect, proven)
- [ ] 30. Restart/recovery test (queued commands survive a process restart)
- [ ] 31. Real OpenTelemetry instrumentation in agent-runtime (replace the plain Event with OTel spans/events)
- [ ] 32. OTel Collector running locally (OTLP ingest)
- [ ] 33. Privacy Gate (allowlist / redact / normalize incoming events)
- [ ] 34. Event Store — separate Postgres DB, append-only, evidence hashes
- [ ] 35. Projection engine (raw events → status/cost/coverage)
- [ ] 36. Observation API (REST snapshot + SSE)
- [ ] 37. Self-hosted Twenty CRM instance available to connect to
- [ ] 38. Twenty read-only connector (scoped API key, REST/GraphQL read)
- [ ] 39. Twenty signed webhook receiver
- [ ] 40. Twenty reconciliation poller (catches anything the webhook missed)
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
