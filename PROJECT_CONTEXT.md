# PROJECT_CONTEXT.md

## Project

**Executive AI Workforce Control Room + Twenty CRM**, built by KeyPillar AI LTD as a licensed product customers self-host.

## Product definition

A secure executive control room providing:

-   read-only AI-agent execution visibility;
-   exactly three V1 controls: PAUSE, STOP, RESUME;
-   read-only Twenty CRM business context;
-   auditable command history;
-   runtime-authoritative proof of applied state;
-   a vendor-side build/licence/update pipeline so KeyPillar can ship signed, licensed releases to customers without ever seeing customer data.

## Authority model

  Truth                Authority
  -------------------- ------------------------
  Execution Truth       Agent Runtime
  Business Truth        Twenty CRM
  Command Truth         Control Plane (agent commands)
  Distribution Truth    Vendor Distribution Plane (KeyPillar cloud)

Core rule: a command is successful only when the registered Agent Runtime proves the resulting state.

Related rule: the vendor proves a deployment is licensed and running a genuine build without ever needing customer telemetry, prompts, or business data.

## Naming note

The source blueprint diagrams label the vendor licensing/build layer a "Product Control Plane." We deliberately call it the **Vendor Distribution Plane** in this project's docs instead, because "Control Plane" is already reserved for the PAUSE/STOP/RESUME agent command system. Same word, two unrelated systems, would have caused real confusion — do not reintroduce the collision.

## Main flows

### Observation

`Agent Runtime → OTel Collector → Privacy Gate → Event Store → Projection/Live API → Executive UI`

### Control (agent commands)

`Executive UI → BFF → Control API → Policy/Step-up → Command Ledger → Transactional Outbox → Dispatcher → Agent Control Adapter → Agent Runtime → Ack/Heartbeat → Reconciliation`

### Twenty

Read-only connector + signed webhook + reconciliation polling.

Twenty never transports control commands.

### Vendor Distribution (Phase 2)

`Private Source + CI → Build + Signing (KMS/HSM) + SBOM → Artifact Registry`
`Artifact Registry → Licence Service → (outbound HTTPS) → Local Licence Verifier`
`Artifact Registry → Update Service → (outbound HTTPS) → Local Update Verifier → admin approval → deployed update`

Outbound HTTPS only from customer to vendor. No inbound vendor tunnel. No telemetry export. No reverse control path.

## UI joins

Relevant entities can be joined using:

-   tenant_id
-   agent_id
-   run_id
-   trace_id
-   crm_record_id

## Runtime control

Supported agents install a small control adapter and expose safe checkpoints.

Opaque/provider-hosted agents are view-only.

## State

``` text
ACTIVE
  |
  +--> PAUSE_REQUESTED --> PAUSED --> RESUME_REQUESTED --> ACTIVE
  |
  +--> STOP_REQUESTED --> STOPPED --> RESUME_REQUESTED --> ACTIVE*
```

Stale heartbeat → `UNKNOWN`.

## Command lifecycle

`REQUESTED → AUTHORIZED → QUEUED → DELIVERED → ACKED → APPLIED`

Alternatives: `REJECTED | EXPIRED | FAILED | UNSUPPORTED`

At-least-once delivery and immutable `command_id` idempotency.

## Command contract

Endpoint:

`POST /control/v1/agents/{agent_id}/commands`

Exact body:

``` json
{
  "action": "PAUSE",
  "expected_state_version": 42,
  "reason": "Executive requested pause"
}
```

## Security

Control/Observation: OIDC, MFA/step-up, RBAC, PostgreSQL RLS, CSRF, append-only audit ledger, signed integrity, mTLS where specified, secret rotation, least privilege, tenant/department isolation.

Vendor Distribution: KMS/HSM build signing, provenance, SBOM, per-tenant licence scoping, outbound-only vendor channel, OIDC/MFA/audit on the Vendor Admin Portal, no rehost of release bytes without a fresh entitlement.

## Failure principle

The system must be honest:

-   requested is not applied;
-   queued is not applied;
-   acknowledged is not automatically applied;
-   only runtime proof makes the command Applied;
-   a vendor cloud outage never silently disables a customer's Observation or Control Plane within the current licence lease window.
