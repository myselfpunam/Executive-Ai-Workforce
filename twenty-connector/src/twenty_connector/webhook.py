from __future__ import annotations

import hashlib
import hmac
import time


class InvalidWebhookSignature(Exception):
    pass


def verify_webhook_signature(
    secret: str,
    timestamp: str,
    raw_body: str,
    provided_signature: str,
    max_age_seconds: float = 300.0,
) -> None:
    """Verifies a Twenty webhook per Twenty's own spec (docs.twenty.com/
    developers/extend/webhooks): HMAC-SHA256 of "{timestamp}:{raw_body}"
    using the shared webhook secret, hex-encoded, compared with a
    timing-safe comparison — never a plain `==`, which leaks timing
    information an attacker could use to guess the signature byte by byte.

    Also rejects a stale (or future) timestamp — Twenty's docs don't
    require this, but without it a captured, genuinely-valid request could
    be replayed by an attacker indefinitely. Raises InvalidWebhookSignature
    with a reason; never silently returns a bool, so a caller can't
    accidentally ignore the result."""
    try:
        timestamp_value = float(timestamp)
    except (TypeError, ValueError) as exc:
        raise InvalidWebhookSignature("timestamp is missing or not a number") from exc

    age = time.time() - timestamp_value
    if abs(age) > max_age_seconds:
        raise InvalidWebhookSignature(f"timestamp is too old or too far in the future (age={age:.1f}s)")

    signed_string = f"{timestamp}:{raw_body}"
    expected_signature = hmac.new(secret.encode("utf-8"), signed_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_signature, provided_signature):
        raise InvalidWebhookSignature("signature does not match")
