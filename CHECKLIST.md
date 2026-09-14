# CHECKLIST.md

## Master checklist

### Phase 1 — Core Control Room

-   [ ] Github Repo
-   [ ] Project Setup
-   [ ] Requirements
-   [ ] Architecture (all four planes documented)
-   [ ] Python AI Agent (Demo) + execution loop
-   [ ] Agent Control SDK — checkpoint, heartbeat, Pause/Stop/Resume
-   [ ] Control API
-   [ ] PostgreSQL Setup
-   [ ] Command Ledger + Outbox
-   [ ] Dispatcher, long-poll, acknowledgement, reconciliation
-   [ ] OpenTelemetry + Observation API + SSE
-   [ ] Twenty CRM read-only integration
-   [ ] Executive Dashboard / frontend
-   [ ] Authentication, RBAC, MFA, RLS
-   [ ] Failure testing, replay, security testing
-   [ ] Phase 1 integration, documentation, deployment, polish

### Phase 2 — Vendor Distribution Plane

-   [ ] Vendor build/CI pipeline + signing (KMS/HSM) + SBOM
-   [ ] Artifact registry
-   [ ] Licence Service + Local Licence Verifier
-   [ ] Update Service + Local Update Verifier
-   [ ] Vendor Admin Portal (OIDC/MFA/audit)
-   [ ] Network isolation proof (no telemetry export, no reverse control path)
-   [ ] Full system integration, documentation, deployment, final polish

## Completion rule

Do not tick an item merely because code exists.

Tick it only when:

-   [ ] implementation works
-   [ ] tests pass
-   [ ] user understands it
-   [ ] architecture boundaries are preserved
-   [ ] security implications are understood
-   [ ] documentation is updated

## Current status

-   Current phase: 1
-   Current week: 3-4
-   Current task: BFF built (TypeScript/Node, proxies Control API + Observation API, honest 502 on upstream failure). 154/154 tests passing overall. Next: the actual dashboard UI.
-   Overall completion: ~44%
