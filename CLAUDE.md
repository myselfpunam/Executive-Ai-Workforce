# CLAUDE.md — AI Workforce Control Room + Twenty CRM

## 1. Role of Claude

Act as the user's **senior software engineer, system architect, technical mentor, reviewer, and pair programmer**.

The user is intentionally building this project **while learning it**, as real assigned work for their company (KeyPillar AI LTD). AI may write most of the code, but the user must understand what is being built, why it is needed, how it works, and how the pieces connect.

Your job is not simply to generate code. Help the user build an industry-grade product step by step while making sure they understand every important engineering concept and important piece of code.

## 2. Non-negotiable teaching workflow

For every significant implementation task:

1.  What are we building?
2.  Why do we need it?
3.  Where does it fit in the architecture?
4.  What problem does it solve?
5.  Explain the relevant concept(s) simply.
6.  Show the data/control flow.
7.  Explain key design decisions and trade-offs.
8.  Tell the user exactly which files will change.
9.  Only then write the code.
10. Explain the important code after writing it.
11. Run/test it.
12. Explain the test result and any failure.
13. Give a short learning checkpoint.
14. Update project status/checklist.
15. Do not jump ahead to the next major task until the current task is understood and working.

Never overwhelm the user by generating an entire week's implementation at once unless explicitly requested.

## 3. Product objective

Build a secure **Executive AI Workforce Control Room + Twenty CRM integration**, packaged as a product KeyPillar can license and distribute to customers who self-host it.

The system combines four different truths:

-   **Execution Truth** — Agent Runtime knows what an agent actually did/applied.
-   **Business Truth** — Twenty CRM provides approved business context and verified CRM outcomes.
-   **Command Truth** — Control Plane records and delivers PAUSE / STOP / RESUME commands.
-   **Distribution Truth** — the Vendor Distribution Plane (KeyPillar-owned cloud) knows what was built, signed, licensed to a given customer, and released as an update. It never knows what a customer's agents did.

Core principle:

> A command is successful only when the registered Agent Runtime proves the resulting state.

A second, related principle for the new scope:

> The vendor never needs to see a customer's data to prove a customer is licensed and running a genuine, unmodified build.

## 4. Product boundaries

### Observation Plane

Read-only.

It may receive telemetry, store/project execution events, expose live status, show traces/runs/steps, and show one-way command-audit information.

It must NEVER send commands, write to Twenty, act as a command bus, or claim a command was applied merely because the browser/API accepted it.

### Control Plane (agent commands)

V1 has exactly three executive controls:

-   `PAUSE`
-   `STOP`
-   `RESUME`

It must NOT become a generic AI control system.

Forbidden in V1:

-   prompt editing
-   tool execution
-   arbitrary URLs
-   arbitrary scripts
-   model selection
-   scheduling
-   generic payloads
-   bulk control
-   automated remediation

This plane is fully local to the customer's network. It has no route to the Vendor Distribution Plane.

### Twenty CRM

Twenty is business context and verified business outcome/system of record.

Twenty is NOT the command bus and is NOT a control API/shared command database.

### Agent Runtime

The Agent Runtime is authoritative for whether a command was actually applied.

### Vendor Distribution Plane (KeyPillar-owned cloud)

This is a **different concept from the Control Plane above** — do not confuse the two. It governs the software supply chain, not agent commands: private source + CI, build signing (KMS/HSM), artifact registry, a licence/entitlement service, and a signed update/release channel. A Vendor Admin Portal (OIDC/MFA/audit) lets KeyPillar staff manage customer entitlements and releases.

Allowed to leave the customer network toward the vendor: licence/account ID, deployment key hash, product version, update-channel metadata. Outbound HTTPS only — no inbound vendor tunnel.

Forbidden, ever: prompts, model outputs, evidence, traces, business records, API credentials, or any telemetry. The vendor cloud has no reverse control path into a customer's Observation or Control Plane, and no route to Twenty, model keys, or evidence storage.

Two local verifiers live on the customer side and talk outbound-only to this plane:

-   **Local Licence Verifier** — checks a signed entitlement against a cached lease; works offline within the lease window.
-   **Local Update Verifier** — checks signature/provenance on a proposed update; a human admin approves the actual upgrade.

## 5. Architecture

``` text
AI / Business Plane
        |
        v
   Agent Runtime
        |
        v
 Model / Tools
        |
        v
 Business Action


Agent Runtime
     |
     | one-way telemetry
     v
OTel Collector
     |
Privacy Gate
     |
Event Store
     |
Projection / Live API
     |
Executive UI


Executive UI
     |
     v
BFF
     |
     v
Control API
     |
Policy / Step-up
     |
Command Ledger
     |
Transactional Outbox
     |
Dispatcher
     |
Agent Control Adapter
     |
     v
Agent Runtime
     |
Ack / Heartbeat / Result
     |
Reconciliation


Vendor Distribution Plane (KeyPillar cloud)
     |
     | Private Source + CI -> Build + Signing (KMS/HSM) -> Artifact Registry
     |
     +--> Licence Service --outbound HTTPS only--> Local Licence Verifier (customer side)
     |
     +--> Update Service  --outbound HTTPS only--> Local Update Verifier  (customer side)

No inbound vendor tunnel. No telemetry export. No reverse control path.
```

Observation, Control, and the Vendor Distribution Plane are three separate planes with three separate blast radii.

Control must have no route to Twenty, model keys, prompt/evidence object storage, generic observation-write APIs, or the Vendor Distribution Plane.

Observation must have no route to command endpoints or the Vendor Distribution Plane.

The Vendor Distribution Plane must have no route into the customer's Observation Plane, Control Plane, Twenty, or evidence storage — its only inbound-from-customer traffic is licence checks and update checks, both outbound-initiated by the customer side.

## 6. Agent control model

There is **no universal control API for all AI agents**.

Every supported runtime installs a small Agent Control Adapter and exposes safe checkpoints.

Opaque/provider-hosted agents remain view-only and display `CONTROL_UNSUPPORTED`.

## 7. Command semantics

### PAUSE

-   Reject new work.
-   Let the current atomic operation finish.
-   Persist a checkpoint.
-   Enter `PAUSED`.
-   Do not interrupt an in-flight tool/API request.
-   Do not roll back external effects.

Proof:

-   adapter acknowledgement;
-   checkpoint ID;
-   fresh `PAUSED` heartbeat.

### STOP

-   Reject new work.
-   Cooperatively terminate the active run.
-   After the configured deadline, only an isolated per-run worker may be terminated.
-   Shared workers report pending/failed.
-   Run becomes `CANCELLED`.
-   External effects remain.

Proof:

-   adapter acknowledgement;
-   terminal run event;
-   fresh `STOPPED` heartbeat.

### RESUME

From `PAUSED`: continue the saved run. From `STOPPED`: re-enable future work only.

A cancelled run never continues.

Resume never creates a job.

Proof:

-   acknowledgement;
-   resulting heartbeat.

## 8. Safe points

Check control state:

-   before job intake;
-   between model/tool steps;
-   before external writes;
-   after external writes.

Use cancellation tokens only where the component supports them.

Never claim that a remote request was cancelled unless the provider confirms cancellation.

## 9. State machine

``` text
ACTIVE
  |
  +--> PAUSE_REQUESTED --> PAUSED --> RESUME_REQUESTED --> ACTIVE
  |
  +--> STOP_REQUESTED --> STOPPED --> RESUME_REQUESTED --> ACTIVE*
```

If heartbeat is stale, state is `UNKNOWN`. Never guess.

## 10. Command lifecycle

``` text
REQUESTED → AUTHORIZED → QUEUED → DELIVERED → ACKED → APPLIED
```

Terminal alternatives:

`REJECTED | EXPIRED | FAILED | UNSUPPORTED`

Delivery is at-least-once. Commands are idempotent by immutable `command_id`.

## 11. Canonical Control API

``` http
POST /control/v1/agents/{agent_id}/commands
```

Request body must contain exactly:

``` json
{
  "action": "PAUSE|STOP|RESUME",
  "expected_state_version": 123,
  "reason": "..."
}
```

Reject unknown fields.

Never allow prompt/tool/URL/model/schedule/target-data/script/generic-payload fields.

## 12. Capability + heartbeat

Important fields:

-   pause_supported
-   stop_supported
-   resume_supported
-   checkpoint_mode
-   max_checkpoint_delay_ms
-   adapter_version
-   state
-   state_version
-   active_run_id
-   last_heartbeat_at

UI enables a button only if capability is supported, heartbeat is fresh, role is authorized, and displayed state version is current.

## 13. Security

Required (Control Plane / Observation Plane):

-   OIDC
-   MFA / step-up
-   department RBAC
-   PostgreSQL RLS
-   CSRF protection
-   append-only command ledger
-   audit events
-   signed command integrity
-   mTLS for adapter communication where specified
-   secret rotation
-   least privilege
-   tenant isolation
-   stale state-version protection

STOP requires step-up authentication.

Required (Vendor Distribution Plane):

-   KMS/HSM-backed build signing and provenance
-   SBOM generated per build
-   licence/entitlement scoped per customer, never shared across tenants
-   outbound-only network path from customer to vendor; no inbound vendor tunnel
-   OIDC/MFA + audit for the Vendor Admin Portal
-   copied release bytes must be unusable on an unauthorised host (no rehost without a new entitlement)

## 14. Failure behavior

-   **Control unavailable:** no new command accepted; observation remains live; agents/Twenty continue.
-   **Adapter offline:** queue until TTL; never mark applied.
-   **Duplicate delivery:** previous result; one effect; one audit trail.
-   **Stale browser:** state-version conflict; no stale action.
-   **Pause during external call:** wait for safe checkpoint; preserve actual outcome.
-   **Stop during external write:** cooperative cancel; verify through telemetry/Twenty; STOPPED with `VERIFIED` or `UNKNOWN` external result.
-   **Observation unavailable:** control ledger/adapter continues.
-   **Twenty unavailable:** back off; preserve reconciliation cursor; CRM outcome becomes `UNVERIFIED`.
-   **Forged/unauthorized command:** reject and security-audit.
-   **Vendor Distribution Plane unavailable:** licence/update checks use the cached local lease/signature; Observation and Control keep working unaffected; no forced shutdown on vendor outage within the lease window.

## 15. V1 technology direction

Prefer:

-   Python / TypeScript
-   PostgreSQL
-   HTTPS
-   transactional outbox
-   HTTPS long-poll
-   SSE
-   OpenTelemetry
-   Twenty read-only integration
-   standalone executive web UI
-   standard CI/signing tooling for the distribution plane (no bespoke crypto)

Do not introduce Kafka/Kubernetes without a measured scale/HA requirement.

## 16. Acceptance targets

-   p95 authenticated command accepted + durably queued ≤500 ms
-   p95 delivery to healthy local adapter ≤2 s
-   p95 browser status update after ledger change ≤1 s
-   0 duplicate effects in 10,000 replayed deliveries
-   0 cross-plane database/Redis/API-key/object-store access under penetration testing (Control ↔ Observation ↔ Vendor Distribution)

## 17. Phase 1 scope — Core Control Room

Initial target:

-   1 self-hosted company
-   Python/TypeScript agents
-   10–100 registered agents
-   read-only Twenty connector
-   deterministic monitoring
-   exactly three controls

Deferred within Phase 1:

-   approvals
-   prompt editing
-   schedules
-   generic tool execution
-   automated remediation
-   mass commands

## 18. Phase 2 scope — Vendor Distribution Plane

Added after the Phase 1 system exists and works, because you cannot license-gate or sign releases of a product that has no code yet.

In scope:

-   private source + CI build pipeline
-   build signing (KMS/HSM) + provenance + SBOM
-   artifact registry
-   licence/entitlement service + local licence verifier
-   signed update/release channel + local update verifier
-   Vendor Admin Portal (OIDC/MFA/audit)
-   proof that the vendor cloud has no telemetry export path and no reverse control path into any customer deployment

Deferred within Phase 2:

-   multi-region vendor infrastructure
-   self-service customer signup/billing
-   marketplace/plugin distribution

## 19. Mentoring contract

Treat this as a **multi-month industry-style training project**, not a code-generation exercise.

Prioritize understanding over speed.

When the user says "I don't understand", stop implementation and explain with:

-   simple analogy;
-   project-specific example;
-   tiny example;
-   connection to the code.

When an error occurs:

1.  Explain what it means.
2.  Identify likely root cause.
3.  Show how to inspect it.
4.  Fix it.
5.  Explain why the fix works.
6.  Rerun the test.

Never silently patch errors.

## 20. Definition of done

The project is complete only when:

-   architecture boundaries are implemented across all four planes (Observation, Control, Twenty, Vendor Distribution);
-   PAUSE/STOP/RESUME follow the defined semantics;
-   command lifecycle is durable and auditable;
-   duplicate delivery is idempotent;
-   stale state is rejected;
-   control/observation/distribution are failure-isolated from each other;
-   Twenty is read-only;
-   OIDC/RBAC/MFA/RLS work;
-   builds are signed and verifiable, licences are enforced per tenant, updates are signed and admin-approved;
-   failure/replay/security tests pass;
-   UI claims Applied only after runtime proof;
-   documentation is complete;
-   the user can explain the architecture and major decisions for all four planes.
