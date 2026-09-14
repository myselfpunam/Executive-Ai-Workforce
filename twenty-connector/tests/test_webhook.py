import hashlib
import hmac
import time

import pytest

from twenty_connector.webhook import InvalidWebhookSignature, verify_webhook_signature

SECRET = "test-webhook-secret"


def _sign(secret: str, timestamp: str, body: str) -> str:
    signed_string = f"{timestamp}:{body}"
    return hmac.new(secret.encode("utf-8"), signed_string.encode("utf-8"), hashlib.sha256).hexdigest()


def test_a_correctly_signed_payload_is_accepted():
    timestamp = str(time.time())
    body = '{"event": "company.created"}'
    signature = _sign(SECRET, timestamp, body)

    verify_webhook_signature(secret=SECRET, timestamp=timestamp, raw_body=body, provided_signature=signature)
    # no exception raised = success


def test_a_wrong_secret_is_rejected():
    timestamp = str(time.time())
    body = '{"event": "company.created"}'
    signature = _sign("wrong-secret", timestamp, body)

    with pytest.raises(InvalidWebhookSignature):
        verify_webhook_signature(secret=SECRET, timestamp=timestamp, raw_body=body, provided_signature=signature)


def test_a_tampered_body_is_rejected_even_with_a_valid_looking_signature():
    timestamp = str(time.time())
    original_body = '{"event": "company.created", "amount": 100}'
    signature = _sign(SECRET, timestamp, original_body)

    tampered_body = '{"event": "company.created", "amount": 100000}'

    with pytest.raises(InvalidWebhookSignature):
        verify_webhook_signature(secret=SECRET, timestamp=timestamp, raw_body=tampered_body, provided_signature=signature)


def test_a_stale_timestamp_is_rejected_even_with_a_correct_signature():
    old_timestamp = str(time.time() - 3600)  # one hour ago
    body = '{"event": "company.created"}'
    signature = _sign(SECRET, old_timestamp, body)

    with pytest.raises(InvalidWebhookSignature):
        verify_webhook_signature(secret=SECRET, timestamp=old_timestamp, raw_body=body, provided_signature=signature)


def test_a_missing_or_malformed_timestamp_is_rejected():
    with pytest.raises(InvalidWebhookSignature):
        verify_webhook_signature(secret=SECRET, timestamp="not-a-number", raw_body="{}", provided_signature="whatever")
