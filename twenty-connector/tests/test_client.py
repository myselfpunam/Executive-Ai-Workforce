import os

import httpx
import pytest

from twenty_connector.client import TwentyClient


def test_list_companies_returns_the_seeded_demo_data(twenty_client):
    companies = twenty_client.list_companies()

    assert isinstance(companies, list)
    assert len(companies) > 0
    assert "name" in companies[0]


def test_list_people_returns_a_list(twenty_client):
    people = twenty_client.list_people()

    assert isinstance(people, list)


def test_an_invalid_api_key_is_rejected():
    bad_client = TwentyClient(base_url=os.environ["TWENTY_API_URL"], api_key="not-a-real-key")
    try:
        with pytest.raises(httpx.HTTPStatusError):
            bad_client.list_companies()
    finally:
        bad_client.close()


def test_the_client_exposes_no_write_operations():
    """Read-only isn't just documented — it's structural. If someone adds
    a create_/update_/delete_ method here later, this test fails on
    purpose, forcing that to be a deliberate, reviewed decision."""
    method_names = [name for name in dir(TwentyClient) if not name.startswith("_")]
    forbidden_prefixes = ("create", "update", "delete", "post", "put", "patch", "write", "remove")

    offending = [name for name in method_names if name.lower().startswith(forbidden_prefixes)]

    assert offending == []
