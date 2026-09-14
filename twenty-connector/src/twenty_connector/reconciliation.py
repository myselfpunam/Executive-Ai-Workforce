from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .client import TwentyClient


@dataclass(frozen=True)
class ReconciliationResult:
    new_or_updated_companies: list[dict]
    new_or_updated_people: list[dict]
    cursor: str  # save this; pass it back in as `since` next time


def _parse_updated_at(record: dict) -> datetime:
    return datetime.fromisoformat(record["updatedAt"].replace("Z", "+00:00"))


def reconcile(client: TwentyClient, since: str | None) -> ReconciliationResult:
    """A safety net alongside the webhook (Step 39) — catches anything a
    dropped/missed webhook delivery would otherwise lose. Compares every
    record's updatedAt against the last cursor and returns only what's
    new or changed since then, plus the new cursor to persist.

    Known simplification: filters client-side after fetching everything,
    rather than asking Twenty's API to filter server-side. Fine at this
    project's scale (10-100 records per CLAUDE.md's V1 scope); would need
    revisiting for a real production-scale CRM."""
    since_dt = datetime.fromisoformat(since.replace("Z", "+00:00")) if since else None

    companies = client.list_companies()
    people = client.list_people()

    def is_new(record: dict) -> bool:
        return since_dt is None or _parse_updated_at(record) > since_dt

    new_companies = [c for c in companies if is_new(c)]
    new_people = [p for p in people if is_new(p)]

    all_timestamps = [r["updatedAt"] for r in (*companies, *people)]
    new_cursor = max(all_timestamps) if all_timestamps else (since or datetime.utcnow().isoformat() + "Z")

    return ReconciliationResult(new_or_updated_companies=new_companies, new_or_updated_people=new_people, cursor=new_cursor)


def load_cursor(path: str | Path) -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text())["cursor"]


def save_cursor(path: str | Path, cursor: str) -> None:
    Path(path).write_text(json.dumps({"cursor": cursor}))
