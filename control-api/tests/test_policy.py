import uuid

import pytest

from control_api.policy import StaleStateVersion, check_and_advance_state_version


def _fresh_agent_id() -> str:
    return f"agent_{uuid.uuid4().hex[:8]}"


def test_a_new_agent_starts_at_version_zero(pg_conn):
    agent_id = _fresh_agent_id()

    with pg_conn.transaction():
        check_and_advance_state_version(pg_conn, agent_id, 0)  # must not raise


def test_the_same_version_cannot_be_used_twice(pg_conn):
    agent_id = _fresh_agent_id()

    with pg_conn.transaction():
        check_and_advance_state_version(pg_conn, agent_id, 0)

    with pytest.raises(StaleStateVersion) as exc_info:
        with pg_conn.transaction():
            check_and_advance_state_version(pg_conn, agent_id, 0)  # stale: already advanced to 1

    assert exc_info.value.expected == 0
    assert exc_info.value.actual == 1


def test_version_advances_by_exactly_one_per_accepted_check(pg_conn):
    agent_id = _fresh_agent_id()

    with pg_conn.transaction():
        check_and_advance_state_version(pg_conn, agent_id, 0)
    with pg_conn.transaction():
        check_and_advance_state_version(pg_conn, agent_id, 1)
    with pg_conn.transaction():
        check_and_advance_state_version(pg_conn, agent_id, 2)


def test_a_failed_check_does_not_advance_the_version(pg_conn):
    agent_id = _fresh_agent_id()

    with pg_conn.transaction():
        check_and_advance_state_version(pg_conn, agent_id, 0)  # now at version 1

    with pytest.raises(StaleStateVersion):
        with pg_conn.transaction():
            check_and_advance_state_version(pg_conn, agent_id, 5)  # wrong guess, rejected

    # still at version 1 — the failed attempt above did not move it
    with pg_conn.transaction():
        check_and_advance_state_version(pg_conn, agent_id, 1)  # proves it, by not raising
