"""Global configuration. Everything has an environment-variable fallback so CI
can be configured without touching test code.

    AIEXPECT_JUDGE       provider:model, e.g. ``ollama:llama3.2``,
                          ``anthropic:claude-opus-5``, ``openai:gpt-4o-mini``,
                          ``openai-compatible:my-model@http://host:8000/v1``
    AIEXPECT_EMBEDDINGS  ``auto`` (default), ``lexical`` or a sentence-transformers model name
    AIEXPECT_JUDGE_TIMEOUT  seconds per judge call (default 300; local models load on first call)
    AIEXPECT_CACHE       ``0`` to disable the on-disk judge cache
    AIEXPECT_CACHE_DIR   where cached judge verdicts live (default ``.aiexpect_cache``)
    AIEXPECT_SNAPSHOT_DIR  where semantic snapshots live (default ``__aisnapshots__``)
    AIEXPECT_SNAPSHOT_MODE ``auto`` (create missing), ``strict`` (fail on missing) or ``update``
    AIEXPECT_HISTORY     run history file for the trend chart (default ``.aiexpect_history.jsonl``)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Settings:
    judge: Optional[str] = None                 # provider spec string, or None for auto-detect
    judge_options: Dict[str, Any] = field(default_factory=dict)
    embeddings: str = "auto"
    similarity_threshold: Optional[float] = None  # None -> backend's own default
    judge_threshold: float = 0.7                  # judge score needed to pass
    cache: bool = True
    cache_dir: str = ".aiexpect_cache"
    ollama_host: str = "http://localhost:11434"
    judge_timeout: float = 300.0                   # seconds per judge call (first call also loads the model)
    text_preview_chars: int = 400                  # how much text the report keeps per check
    snapshot_dir: str = "__aisnapshots__"
    snapshot_mode: str = "auto"                    # auto: create missing | strict: fail on missing | update: overwrite
    history_path: str = ".aiexpect_history.jsonl"  # run-over-run Trust Score history ("" disables)
    history_runs: int = 30                         # how many past runs the trend chart shows

    @classmethod
    def from_env(cls) -> Settings:
        s = cls()
        s.judge = os.environ.get("AIEXPECT_JUDGE") or None
        s.embeddings = os.environ.get("AIEXPECT_EMBEDDINGS", "auto")
        s.cache = os.environ.get("AIEXPECT_CACHE", "1") not in ("0", "false", "no")
        s.cache_dir = os.environ.get("AIEXPECT_CACHE_DIR", ".aiexpect_cache")
        s.ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        if not s.ollama_host.startswith("http"):
            s.ollama_host = "http://" + s.ollama_host
        s.snapshot_dir = os.environ.get("AIEXPECT_SNAPSHOT_DIR", "__aisnapshots__")
        s.snapshot_mode = os.environ.get("AIEXPECT_SNAPSHOT_MODE", "auto")
        s.history_path = os.environ.get("AIEXPECT_HISTORY", ".aiexpect_history.jsonl")
        to = os.environ.get("AIEXPECT_JUDGE_TIMEOUT")
        if to:
            s.judge_timeout = float(to)
        thr = os.environ.get("AIEXPECT_JUDGE_THRESHOLD")
        if thr:
            s.judge_threshold = float(thr)
        return s


settings = Settings.from_env()


def configure(**kwargs: Any) -> Settings:
    """Override settings at runtime, e.g. in ``conftest.py``::

        import aiexpect
        aiexpect.configure(judge="ollama:llama3.2", judge_threshold=0.6)
    """
    from .backends import embeddings, judges  # local import to avoid cycles

    for k, v in kwargs.items():
        if not hasattr(settings, k):
            raise TypeError(f"Unknown aiexpect setting: {k!r}")
        setattr(settings, k, v)
    judges.reset()
    embeddings.reset()
    return settings
