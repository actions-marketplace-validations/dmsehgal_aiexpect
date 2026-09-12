"""Semantic snapshot testing.

    expect(reply).to_match_snapshot()

First run stores the reply under ``__aisnapshots__/<test id>.json``. Later runs
compare the new reply to the stored one **by meaning** (Tier 2 similarity), so
harmless rewording passes and a real change in what the bot says fails. Refresh
with ``pytest --aiexpect-update-snapshots``; forbid silent creation in CI with
``--aiexpect-snapshot-mode=strict``.
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, Optional

from .config import settings

_UNSAFE = re.compile(r"[^A-Za-z0-9_.-]+")
_counters: Dict[str, int] = {}


def reset_counters() -> None:
    _counters.clear()


def snapshot_key(test_id: str, name: Optional[str]) -> str:
    """Stable file-safe key. Multiple unnamed snapshots in one test get a suffix."""
    base = test_id or "snapshot"
    if name:
        return _UNSAFE.sub("_", f"{base}__{name}").strip("_")
    n = _counters.get(base, 0)
    _counters[base] = n + 1
    return _UNSAFE.sub("_", base if n == 0 else f"{base}__{n + 1}").strip("_")


def snapshot_path(key: str) -> str:
    return os.path.join(settings.snapshot_dir, key + ".json")


def load(key: str) -> Optional[dict]:
    p = snapshot_path(key)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(key: str, text: str, meta: Optional[dict] = None) -> str:
    p = snapshot_path(key)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"text": text, **(meta or {})}, f, indent=2, ensure_ascii=False)
    return p
