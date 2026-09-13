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
- [ ] 14. Package 8–13 into `control-sdk-python/` as a reusable library ← **next**
- [ ] 15. Cancellation token support for cooperative STOP
- [ ] 16. Port the same SDK contract to `control-sdk-ts/` (TypeScript)
- [ ] 17. Freeze the command JSON schema + error codes (the exact contract from CLAUDE.md §11)
- [ ] 18. PostgreSQL running locally (Control DB)
- [ ] 19. Command ledger table (append-only)
- [ ] 20. Transactional outbox table + pattern
- [ ] 21. Control API skeleton — `POST /control/v1/agents/{agent_id}/commands`
- [ ] 22. Policy engine (tenant/department scope, expected_state_version check)
- [ ] 23. Step-up check for STOP (basic version, before full MFA)
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
