from __future__ import annotations

import httpx


class TwentyClient:
    """Read-only access to a Twenty CRM workspace.

    CLAUDE.md sections 4/6: Twenty is business context and verified
    outcome — never a command bus, never written to by this system. This
    class deliberately exposes ONLY read (GET) methods; there is no
    create/update/delete here by design, not merely by convention.

    Important: Twenty's own API key is full-access (no read-only key type
    in this version) — Twenty itself does not enforce read-only. This
    class is what actually enforces it, so never add a write method here
    without a real, deliberate architecture decision to change that."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    def list_companies(self, limit: int = 50) -> list[dict]:
        response = self._client.get("/rest/companies", params={"limit": limit})
        response.raise_for_status()
        return response.json()["data"]["companies"]

    def list_people(self, limit: int = 50) -> list[dict]:
        response = self._client.get("/rest/people", params={"limit": limit})
        response.raise_for_status()
        return response.json()["data"]["people"]

    def list_opportunities(self, limit: int = 50) -> list[dict]:
        response = self._client.get("/rest/opportunities", params={"limit": limit})
        response.raise_for_status()
        return response.json()["data"]["opportunities"]

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TwentyClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
