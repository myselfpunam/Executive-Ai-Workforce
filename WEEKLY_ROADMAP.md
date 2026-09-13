# WEEKLY_ROADMAP.md — 25 Weeks / 20 Hours Per Week

Target: approximately **500 hours**, split into Phase 1 (core control room, weeks 1–20) and Phase 2 (vendor distribution/licensing, weeks 21–25).

Weekly split:

-   12h concept + coding
-   4h debugging/problem solving
-   2h testing
-   2h documentation/revision

Slow down if understanding is incomplete. This is real assigned company work — there is no reward for rushing past a concept you don't actually understand.

# Phase 1 — Core Control Room

## Week 1–2 — Architecture, Git, Setup, Requirements

Learn:

-   Git/GitHub
-   repository structure
-   local development
-   environment variables
-   requirements analysis
-   architecture
-   API/service/database basics

Build:

-   repository
-   development environment
-   requirements docs
-   architecture docs (now covering all four planes: Observation, Control, Twenty, Vendor Distribution)

Exit: User can explain Observation, Control, Twenty, and Vendor Distribution boundaries, and why "Control Plane" and "Vendor Distribution Plane" are not the same thing.

## Week 3–4 — Python AI Agent Demo + Execution Loop

Learn:

-   Python application structure
-   execution loop
-   model/tool abstraction
-   run/step
-   structured events

Build:

-   deterministic demo agent
-   execution loop
-   observable steps
-   run IDs

Exit: User understands run, step, execution and safe-point concepts.

## Week 5–7 — Agent Control SDK

Learn:

-   state machines
-   safe checkpoints
-   cooperative cancellation
-   heartbeat
-   capability advertisement
-   idempotency
-   command inbox

Build:

-   control adapter/SDK
-   PAUSE
-   STOP
-   RESUME
-   checkpoint persistence
-   heartbeat
-   capabilities
-   idempotent command handling

Exit: Pause/Stop/Resume semantics work and are understood.

## Week 8–10 — Control API + PostgreSQL + Ledger + Outbox

Learn:

-   REST
-   PostgreSQL
-   transactions
-   constraints
-   optimistic concurrency
-   append-only ledger
-   transactional outbox

Build:

-   Control API
-   policy
-   database schema
-   command ledger
-   outbox

Exit: Valid commands queue durably; invalid/stale commands are rejected.

## Week 11–12 — Dispatcher + Long-Poll + Ack + Reconciliation

Learn:

-   at-least-once delivery
-   retries
-   leases
-   long-polling
-   acknowledgements
-   reconciliation
-   distributed failure modes

Build:

-   dispatcher
-   long-poll
-   adapter delivery
-   acknowledgement
-   reconciliation

Exit: Duplicate delivery causes one effect; restart recovers queued work.

## Week 13–14 — OpenTelemetry + Observation API + SSE

Learn:

-   traces/spans
-   events
-   privacy filtering
-   event projection
-   SSE

Build:

-   OTel path
-   privacy gate
-   event store
-   Observation API
-   SSE

Exit: Observation works independently of control.

## Week 15 — Twenty CRM Read-Only Integration

Learn:

-   external APIs
-   scoped credentials
-   webhooks
-   reconciliation

Build:

-   read-only connector
-   schema discovery
-   signed webhook handling
-   reconciliation poller

Exit: Twenty supplies context/outcome only.

## Week 16–17 — Executive Dashboard / Frontend

Learn:

-   frontend architecture
-   authenticated sessions
-   SSE
-   authoritative UI state
-   confirmation UX

Build:

-   executive dashboard
-   agent/run/step views
-   CRM context
-   command controls
-   command proof/status UI

Exit: UI never says Applied before runtime proof.

## Week 18 — Authentication, RBAC, MFA, RLS

Learn:

-   OIDC
-   MFA/step-up
-   RBAC
-   PostgreSQL RLS
-   CSRF

Build:

-   authenticated BFF
-   role enforcement
-   STOP step-up
-   department restrictions
-   RLS
-   audit context

Exit: Unauthorized/cross-department access fails.

## Week 19 — Failure, Replay, Security Testing

Test:

-   restart
-   stale state
-   duplicate delivery
-   network partition
-   adapter offline
-   observation outage
-   Twenty outage
-   disk pressure
-   forged command
-   replay
-   cross-role
-   cross-department

Exit: No false success and no duplicate effects.

## Week 20 — Phase 1 Integration, Documentation, Deployment, Polish

Complete:

-   end-to-end demo of Observation + Control + Twenty
-   deployment
-   API docs
-   runbook
-   security notes
-   test report
-   Phase 1 README

Exit: User can explain and defend the Phase 1 system in an interview. This is the point where Phase 1 is a real, working, self-hostable product — before any licensing/distribution work begins.

# Phase 2 — Vendor Distribution Plane

Deliberately sequenced after Phase 1 works: you cannot sign, license, or gate updates for a product that does not exist yet.

## Week 21 — Vendor Build, Signing & Artifact Registry

Learn:

-   CI/CD pipeline design
-   build provenance (SLSA-style thinking)
-   code signing with KMS/HSM
-   SBOM generation
-   artifact registries

Build:

-   private source + CI pipeline
-   build signing step (KMS/HSM-backed key)
-   SBOM generation per build
-   artifact registry storing signed OCI artifacts

Exit: User can explain what a signature proves (build authenticity) versus what it does not prove (licence/entitlement), and why those are separate concerns.

## Week 22 — Licence Service + Local Licence Verifier

Learn:

-   entitlement modeling (customer/deployment scoping)
-   signed licence tokens
-   offline-tolerant verification (cached leases)
-   revocation

Build:

-   Licence Service (vendor side): issues signed, scoped entitlements
-   Local Licence Verifier (customer side): verifies signature, checks cached lease, works offline within the lease window

Exit: A deployment without a valid licence fails closed in a defined, honest way (not a silent crash); a valid licence works even if the vendor cloud is briefly unreachable.

## Week 23 — Update Service + Local Update Verifier

Learn:

-   signed release channels
-   provenance verification on the client side
-   admin-gated rollout (no silent auto-apply)

Build:

-   Update Service (vendor side): publishes signed release metadata
-   Local Update Verifier (customer side): verifies signature/provenance, surfaces the update to a human admin for approval

Exit: An unsigned or tampered update is rejected locally without any vendor round-trip needed to detect it.

## Week 24 — Vendor Admin Portal + Network Isolation Proof

Learn:

-   OIDC/MFA for internal vendor tooling
-   audit logging for a privileged internal tool
-   network segmentation testing

Build:

-   Vendor Admin Portal (OIDC/MFA/audit) for managing customer entitlements and releases
-   automated check proving: no telemetry export path and no reverse control path exist between the vendor cloud and any customer deployment

Exit: User can demonstrate, not just claim, that the vendor cloud cannot see customer data or issue commands into a customer deployment.

## Week 25 — Full System Integration, Documentation, Deployment, Final Polish

Complete:

-   end-to-end demo covering Observation + Control + Twenty + Licensing/Updates
-   deployment guide for a new customer install
-   API docs (Control API, Licence Service, Update Service)
-   runbook
-   security notes (Phase 1 + Phase 2)
-   test report
-   final README
-   final demo scenario

Exit: User can explain and defend the entire system, including why Phase 2 exists and how it stays isolated from Phase 1, in an interview.
