"""Global configuration. Everything has an environment-variable fallback so CI
can be configured without touching test code.

    LLMEXPECT_JUDGE       provider:model, e.g. ``ollama:llama3.1``,
                          ``anthropic:claude-opus-5``, ``openai:gpt-4o-mini``,
                          ``openai-compatible:my-model@http://host:8000/v1``
    LLMEXPECT_EMBEDDINGS  ``auto`` (default), ``lexical`` or a sentence-transformers model name
    LLMEXPECT_CACHE       ``0`` to disable the on-disk judge cache
    LLMEXPECT_CACHE_DIR   where cached judge verdicts live (default ``.llmexpect_cache``)
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
    cache_dir: str = ".llmexpect_cache"
    ollama_host: str = "http://localhost:11434"
    text_preview_chars: int = 400                  # how much text the report keeps per check

    @classmethod
    def from_env(cls) -> Settings:
        s = cls()
        s.judge = os.environ.get("LLMEXPECT_JUDGE") or None
        s.embeddings = os.environ.get("LLMEXPECT_EMBEDDINGS", "auto")
        s.cache = os.environ.get("LLMEXPECT_CACHE", "1") not in ("0", "false", "no")
        s.cache_dir = os.environ.get("LLMEXPECT_CACHE_DIR", ".llmexpect_cache")
        s.ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        if not s.ollama_host.startswith("http"):
            s.ollama_host = "http://" + s.ollama_host
        thr = os.environ.get("LLMEXPECT_JUDGE_THRESHOLD")
        if thr:
            s.judge_threshold = float(thr)
        return s


settings = Settings.from_env()


def configure(**kwargs: Any) -> Settings:
    """Override settings at runtime, e.g. in ``conftest.py``::

        import llmexpect
        llmexpect.configure(judge="ollama:llama3.1", judge_threshold=0.6)
    """
    from .backends import embeddings, judges  # local import to avoid cycles

    for k, v in kwargs.items():
        if not hasattr(settings, k):
            raise TypeError(f"Unknown llmexpect setting: {k!r}")
        setattr(settings, k, v)
    judges.reset()
    embeddings.reset()
    return settings
