import uuid

from fastapi.testclient import TestClient

from control_api.app import app

client = TestClient(app)


def _url(agent_id: str) -> str:
    return f"/control/v1/agents/{agent_id}/commands"


def _fresh_agent_id() -> str:
    return f"agent_{uuid.uuid4().hex[:8]}"


def test_stop_without_a_step_up_token_is_rejected_with_401():
    body = {"action": "STOP", "expected_state_version": 0, "reason": "test"}

    response = client.post(_url(_fresh_agent_id()), json=body)

    assert response.status_code == 401
    assert response.json()["code"] == "STEP_UP_REQUIRED"


def test_stop_with_the_wrong_step_up_token_is_rejected_with_401():
    body = {"action": "STOP", "expected_state_version": 0, "reason": "test"}

    response = client.post(_url(_fresh_agent_id()), json=body, headers={"X-Step-Up-Token": "guessed-wrong"})

    assert response.status_code == 401
    assert response.json()["code"] == "STEP_UP_REQUIRED"


def test_stop_with_the_correct_step_up_token_is_accepted():
    body = {"action": "STOP", "expected_state_version": 0, "reason": "test"}

    response = client.post(_url(_fresh_agent_id()), json=body, headers={"X-Step-Up-Token": "dev-step-up-token"})

    assert response.status_code == 202


def test_pause_never_requires_a_step_up_token():
    body = {"action": "PAUSE", "expected_state_version": 0, "reason": "test"}

    response = client.post(_url(_fresh_agent_id()), json=body)  # no header at all

    assert response.status_code == 202


def test_resume_never_requires_a_step_up_token():
    body = {"action": "RESUME", "expected_state_version": 0, "reason": "test"}

    response = client.post(_url(_fresh_agent_id()), json=body)  # no header at all

    assert response.status_code == 202
