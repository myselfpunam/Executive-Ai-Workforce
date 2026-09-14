from __future__ import annotations

import os
import pathlib

import psycopg
import pytest


def _load_env_file(path: pathlib.Path) -> None:
    """Minimal .env loader — no extra dependency for something this small."""
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
def pg_conn():
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    try:
        yield conn
    finally:
        conn.close()
