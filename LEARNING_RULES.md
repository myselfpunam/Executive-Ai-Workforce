# LEARNING_RULES.md

## Principle

The user is using AI as a coding partner, not as a substitute for understanding. This is real assigned company work — understanding it is part of the job, not optional extra credit.

## Rule 1 — Explain before code

Before significant code, explain:

-   goal
-   reason
-   architecture location
-   concept
-   flow
-   design choice

## Rule 2 — Small increments

Prefer one feature, one or two files, one testable behavior, one checkpoint.

## Rule 3 — Confirm understanding

After an important feature, ask the user to explain:

-   what it does;
-   why it exists;
-   what happens on failure;
-   which component is authoritative.

## Rule 4 — Debug transparently

Explain symptom → root cause → fix → prevention.

## Rule 5 — Avoid fake complexity

Do not add microservices, Kafka, Kubernetes or abstractions without a measured reason.

## Rule 6 — Production mindset

Consider:

-   security
-   failure
-   idempotency
-   observability
-   testing
-   recovery
-   auditability

## Rule 7 — Preserve boundaries

Observation is read-only.

Twenty is not command transport.

Runtime proves applied state.

V1 control is only PAUSE/STOP/RESUME.

The Vendor Distribution Plane never sees customer telemetry, prompts, evidence, or business data, and has no reverse route into the customer's Observation or Control Plane.

## Rule 8 — No false success

Requested, authorized, queued, delivered and acknowledged are different from Applied.

Applied requires runtime proof.

A licence check passing is not the same as a build being genuine — provenance/signature verification is separate from entitlement verification.

## Rule 9 — Interview readiness

At major milestones prepare:

-   30-second explanation
-   2-minute explanation
-   architecture diagram
-   interview questions
-   trade-offs

## Rule 10 — Documentation is engineering

Keep README, architecture docs, API docs, decision records, test notes, security notes, runbooks and checklist current.

## Rule 11 — Flag conflicts, don't silently resolve them

When a new document, diagram, or instruction conflicts with an existing one (naming, scope, or architecture), surface the conflict and ask which one is authoritative before proceeding. Do not guess and do not quietly pick one.
