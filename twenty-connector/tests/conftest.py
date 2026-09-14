from __future__ import annotations

import os
import pathlib

import pytest

from twenty_connector.client import TwentyClient


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
def twenty_client():
    client = TwentyClient(base_url=os.environ["TWENTY_API_URL"], api_key=os.environ["TWENTY_API_KEY"])
    try:
        yield client
    finally:
        client.close()
