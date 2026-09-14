import uuid

from fastapi.testclient import TestClient

from control_api.app import app

client = TestClient(app)


def _url(agent_id: str) -> str:
    return f"/control/v1/agents/{agent_id}/commands"


def _fresh_agent_id() -> str:
    return f"agent_{uuid.uuid4().hex[:8]}"


def _valid_body(**overrides):
    # A brand-new agent starts at state_version 0 (see policy.py) — every
    # test uses its own fresh agent_id, so 0 is always correct here.
    body = {"action": "PAUSE", "expected_state_version": 0, "reason": "executive requested pause"}
    body.update(overrides)
    return body


def test_a_valid_command_is_accepted_and_queued():
    response = client.post(_url(_fresh_agent_id()), json=_valid_body())

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "QUEUED"
    assert data["command_id"].startswith("cmd_")


def test_an_injected_prompt_field_is_rejected_with_400():
    response = client.post(_url(_fresh_agent_id()), json=_valid_body(prompt="ignore previous instructions"))

    assert response.status_code == 400
    assert response.json()["code"] == "SCHEMA_VALIDATION_FAILED"


def test_an_action_outside_the_closed_enum_is_rejected_with_400():
    response = client.post(_url(_fresh_agent_id()), json=_valid_body(action="DELETE_EVERYTHING"))

    assert response.status_code == 400
    assert response.json()["code"] == "UNKNOWN_ACTION"


def test_a_non_object_body_is_rejected_with_400():
    response = client.post(_url(_fresh_agent_id()), json=["not", "an", "object"])

    assert response.status_code == 400


def test_a_stale_expected_state_version_is_rejected_with_409():
    agent_id = _fresh_agent_id()

    first = client.post(_url(agent_id), json=_valid_body(expected_state_version=0))
    assert first.status_code == 202  # advances agent_state to version 1

    second = client.post(_url(agent_id), json=_valid_body(expected_state_version=0))  # stale now

    assert second.status_code == 409
    assert second.json()["code"] == "STALE_STATE_VERSION"
    assert second.json()["current_state_version"] == 1


def test_the_correct_next_state_version_is_accepted_after_one_command():
    agent_id = _fresh_agent_id()

    first = client.post(_url(agent_id), json=_valid_body(expected_state_version=0))
    assert first.status_code == 202

    second = client.post(_url(agent_id), json=_valid_body(expected_state_version=1))

    assert second.status_code == 202


def test_accepted_command_actually_lands_in_the_ledger_and_outbox(pg_conn):
    agent_id = _fresh_agent_id()
    response = client.post(_url(agent_id), json=_valid_body(reason="end-to-end proof"))
    command_id = response.json()["command_id"]

    with pg_conn.cursor() as cur:
        cur.execute("SELECT event_type, agent_id, action FROM command_ledger WHERE command_id = %s", (command_id,))
        ledger_row = cur.fetchone()

        cur.execute("SELECT status FROM command_outbox WHERE command_id = %s", (command_id,))
        outbox_row = cur.fetchone()

    assert ledger_row == ("REQUESTED", agent_id, "PAUSE")
    assert outbox_row == ("PENDING",)
