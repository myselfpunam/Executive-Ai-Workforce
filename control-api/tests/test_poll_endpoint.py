import threading
import time
import uuid

from fastapi.testclient import TestClient

from control_api.app import app

client = TestClient(app)


def _fresh_agent_id() -> str:
    return f"agent_{uuid.uuid4().hex[:8]}"


def _submit(agent_id: str, action: str = "PAUSE", expected_state_version: int = 0):
    return client.post(
        f"/control/v1/agents/{agent_id}/commands",
        json={"action": action, "expected_state_version": expected_state_version, "reason": "poll test"},
    )


def _poll_url(agent_id: str, timeout_seconds: float, poll_interval_seconds: float) -> str:
    return (
        f"/control/v1/agents/{agent_id}/commands/poll"
        f"?timeout_seconds={timeout_seconds}&poll_interval_seconds={poll_interval_seconds}"
    )


def test_poll_returns_immediately_when_a_command_is_already_pending():
    agent_id = _fresh_agent_id()
    submitted = _submit(agent_id)
    assert submitted.status_code == 202

    start = time.monotonic()
    response = client.get(_poll_url(agent_id, timeout_seconds=5, poll_interval_seconds=0.05))
    elapsed = time.monotonic() - start

    assert response.status_code == 200
    assert response.json()["command"]["command_id"] == submitted.json()["command_id"]
    assert elapsed < 1.0  # did not wait for the timeout — it was already there


def test_poll_times_out_with_no_command_when_nothing_ever_arrives():
    agent_id = _fresh_agent_id()  # nobody ever submits anything for this agent

    start = time.monotonic()
    response = client.get(_poll_url(agent_id, timeout_seconds=0.3, poll_interval_seconds=0.05))
    elapsed = time.monotonic() - start

    assert response.status_code == 200
    assert response.json()["command"] is None
    assert elapsed >= 0.3


def test_poll_waits_and_returns_a_command_that_arrives_mid_wait():
    agent_id = _fresh_agent_id()

    def submit_after_delay():
        time.sleep(0.3)
        _submit(agent_id)

    submitter = threading.Thread(target=submit_after_delay)
    submitter.start()

    start = time.monotonic()
    response = client.get(_poll_url(agent_id, timeout_seconds=3, poll_interval_seconds=0.05))
    elapsed = time.monotonic() - start
    submitter.join()

    assert response.status_code == 200
    assert response.json()["command"] is not None
    # proves it was genuinely waiting, not returning instantly and not
    # hitting the full 3s timeout either
    assert 0.25 < elapsed < 2.0


def test_full_lifecycle_so_far_is_recorded_in_order_in_the_ledger(pg_conn):
    agent_id = _fresh_agent_id()
    submitted = _submit(agent_id)
    command_id = submitted.json()["command_id"]

    poll_response = client.get(_poll_url(agent_id, timeout_seconds=2, poll_interval_seconds=0.05))
    assert poll_response.json()["command"]["command_id"] == command_id

    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT event_type FROM command_ledger WHERE command_id = %s ORDER BY ledger_id",
            (command_id,),
        )
        event_types = [row[0] for row in cur.fetchall()]

    assert event_types == ["REQUESTED", "DELIVERED"]
