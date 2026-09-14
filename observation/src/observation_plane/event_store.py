from __future__ import annotations

import hashlib
import json

import psycopg
from psycopg.types.json import Json

from .privacy_gate import ObservationEvent

GENESIS_HASH = "0" * 64


def _canonical_json(event: ObservationEvent) -> str:
    return json.dumps(
        {
            "trace_id": event.trace_id,
            "span_id": event.span_id,
            "parent_span_id": event.parent_span_id,
            "name": event.name,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "status": event.status,
            "attributes": event.attributes,
        },
        sort_keys=True,
    )


def compute_evidence_hash(event: ObservationEvent, previous_hash: str) -> str:
    """Chains each event to the one before it: sha256(previous_hash + this
    event's canonical content). Changing ANY past event, even by one
    character, changes its hash and therefore every hash after it — that
    makes tampering detectable, not just disallowed by convention."""
    payload = previous_hash + _canonical_json(event)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def store_event(conn: psycopg.Connection, event: ObservationEvent) -> str:
    """Appends one gated event to the store, chained to the current latest
    hash. Returns the new evidence_hash."""
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("SELECT evidence_hash FROM observation_events ORDER BY event_id DESC LIMIT 1 FOR UPDATE")
            row = cur.fetchone()
            previous_hash = row[0] if row else GENESIS_HASH

            evidence_hash = compute_evidence_hash(event, previous_hash)

            cur.execute(
                """
                INSERT INTO observation_events
                    (trace_id, span_id, parent_span_id, name, start_time, end_time, status,
                     attributes, previous_hash, evidence_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event.trace_id,
                    event.span_id,
                    event.parent_span_id,
                    event.name,
                    event.start_time,
                    event.end_time,
                    event.status,
                    Json(event.attributes),
                    previous_hash,
                    evidence_hash,
                ),
            )

    return evidence_hash


def verify_chain_integrity(conn: psycopg.Connection) -> bool:
    """Recomputes every hash from scratch and confirms it matches what was
    stored. This is how tampering gets detected even if someone bypassed
    the append-only trigger directly (e.g. a database superuser disabling
    it) — the hash chain is an independent safeguard, not dependent on the
    trigger holding."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT trace_id, span_id, parent_span_id, name, start_time, end_time, status,
                   attributes, previous_hash, evidence_hash
            FROM observation_events ORDER BY event_id
            """
        )
        rows = cur.fetchall()

    for row in rows:
        (
            trace_id, span_id, parent_span_id, name, start_time, end_time, status,
            attributes, previous_hash, stored_hash,
        ) = row
        event = ObservationEvent(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            start_time=start_time,
            end_time=end_time,
            status=status,
            attributes=attributes,
        )
        if compute_evidence_hash(event, previous_hash) != stored_hash:
            return False

    return True
