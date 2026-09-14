from datetime import datetime, timedelta, timezone

from twenty_connector.reconciliation import load_cursor, reconcile, save_cursor


def test_first_reconciliation_with_no_cursor_returns_all_existing_records(twenty_client):
    result = reconcile(twenty_client, since=None)

    assert len(result.new_or_updated_companies) > 0  # the seeded demo data
    assert result.cursor  # a cursor was produced to save for next time


def test_a_cursor_far_in_the_future_returns_nothing_new(twenty_client):
    far_future = (datetime.now(timezone.utc) + timedelta(days=3650)).isoformat()

    result = reconcile(twenty_client, since=far_future)

    assert result.new_or_updated_companies == []
    assert result.new_or_updated_people == []


def test_reconciling_again_with_the_returned_cursor_finds_nothing_new(twenty_client):
    first = reconcile(twenty_client, since=None)

    second = reconcile(twenty_client, since=first.cursor)

    assert second.new_or_updated_companies == []
    assert second.new_or_updated_people == []


def test_cursor_round_trips_through_save_and_load(tmp_path):
    path = tmp_path / "twenty_cursor.json"
    assert load_cursor(path) is None  # nothing saved yet

    save_cursor(path, "2026-09-14T15:00:00+00:00")

    assert load_cursor(path) == "2026-09-14T15:00:00+00:00"
