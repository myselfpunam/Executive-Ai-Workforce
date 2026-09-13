# vendor-distribution

**Plane:** Vendor Distribution Plane (Distribution Truth) — KeyPillar-owned cloud. Not to be confused with the agent Control Plane in `control-api/`.

**Role:** private source + CI build pipeline, build signing (KMS/HSM) + SBOM, artifact registry, Licence Service + Local Licence Verifier, Update Service + Local Update Verifier, and the Vendor Admin Portal. Outbound HTTPS only from customer to vendor; no inbound vendor tunnel; no telemetry export; no reverse control path into any customer deployment.

**Status:** not started — Phase 2, Week 21-24 of the roadmap. Deliberately built after the Phase 1 system works — there is nothing to license or sign a release of yet.

**Depends on:** the entire Phase 1 system (`agent-runtime/` through `web/`) existing as a real, working product.
