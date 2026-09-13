# twenty-connector

**Plane:** Twenty CRM (Business Truth), read-only.

**Role:** scoped read-only API access to Twenty, signed webhook handling for fast create/update/delete signals, and a reconciliation poller for anything the webhook missed. Never transports control commands; never becomes a shared database with the Control Plane.

**Status:** not started — Week 15 of the roadmap.

**Depends on:** a running, self-hosted Twenty CRM instance to connect to.
