from __future__ import annotations

import os
import pathlib

import psycopg
import pytest


def _load_env_file(path: pathlib.Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key, value)


_load_env_file(pathlib.Path(__file__).resolve().parents[1] / ".env")


@pytest.fixture
def database_url() -> str:
    return os.environ["DATABASE_URL"]


@pytest.fixture
def pg_conn():
    # autocommit=True: a plain, un-wrapped execute() (common in test setup
    # and assertions) commits immediately instead of silently opening a
    # transaction that never closes — which would make writes invisible
    # to OTHER connections (like the one stream_events opens internally)
    # until something eventually committed it. `with conn.transaction()`
    # blocks (used by our real application code) still work correctly on
    # an autocommit connection — psycopg3 handles that explicitly.
    conn = psycopg.connect(os.environ["DATABASE_URL"], autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def superuser_conn():
    """A superuser connection (local peer auth, OS user) — used only to
    simulate an attacker/operator bypassing the append-only trigger
    directly, to prove the hash chain catches it independently."""
    conn = psycopg.connect(dbname="executive_observation_dev")
    try:
        yield conn
    finally:
        conn.close()
