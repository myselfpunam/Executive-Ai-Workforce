import hashlib
import hmac
import os
import time

from fastapi.testclient import TestClient

from twenty_connector.app import app

client = TestClient(app)


def _sign(secret: str, timestamp: str, body: str) -> str:
    signed_string = f"{timestamp}:{body}"
    return hmac.new(secret.encode("utf-8"), signed_string.encode("utf-8"), hashlib.sha256).hexdigest()


def test_a_correctly_signed_webhook_is_acknowledged_with_200():
    secret = os.environ["TWENTY_WEBHOOK_SECRET"]
    body = '{"event": "company.created", "companyId": "abc123"}'
    timestamp = str(time.time())
    signature = _sign(secret, timestamp, body)

    response = client.post(
        "/twenty/webhook",
        content=body,
        headers={
            "content-type": "application/json",
            "x-twenty-webhook-timestamp": timestamp,
            "x-twenty-webhook-signature": signature,
        },
    )

    assert response.status_code == 200


def test_a_forged_webhook_with_the_wrong_signature_is_rejected_with_401():
    body = '{"event": "company.created", "companyId": "abc123"}'
    timestamp = str(time.time())

    response = client.post(
        "/twenty/webhook",
        content=body,
        headers={
            "content-type": "application/json",
            "x-twenty-webhook-timestamp": timestamp,
            "x-twenty-webhook-signature": "0" * 64,  # a plausible-looking but wrong signature
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_WEBHOOK_SIGNATURE"


def test_a_webhook_with_no_signature_header_at_all_is_rejected():
    response = client.post("/twenty/webhook", content="{}", headers={"content-type": "application/json"})

    assert response.status_code == 401
