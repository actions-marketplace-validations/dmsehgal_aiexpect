from __future__ import annotations

import json
import platform
import time
from typing import Any, Dict, List

from ..results import CheckResult, summarize


def build_payload(results: List[CheckResult], meta: Dict[str, Any] = None, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    from .. import __version__

    return {
        "history": history or [],
        "tool": "aiexpect",
        "version": __version__,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python": platform.python_version(),
        "meta": meta or {},
        "summary": summarize(results),
        "checks": [r.to_dict() for r in results],
    }


def write_json(path: str, results: List[CheckResult], meta: Dict[str, Any] = None, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = build_payload(results, meta, history)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return payload
