"""Run-over-run history for the trend chart. One JSON line per session."""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

from .config import settings


def append(summary: Dict[str, Any], path: str = "") -> None:
    path = path or settings.history_path
    if not path:
        return
    row = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "trust_score": summary.get("trust_score"),
        "subscores": summary.get("subscores", {}),
        "total_checks": summary.get("total_checks", 0),
        "passed_checks": summary.get("passed_checks", 0),
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def load(path: str = "", limit: int = 0) -> List[Dict[str, Any]]:
    path = path or settings.history_path
    limit = limit or settings.history_runs
    if not path or not os.path.exists(path):
        return []
    rows: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows[-limit:]
