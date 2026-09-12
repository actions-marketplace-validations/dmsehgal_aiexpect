"""Tier 3: LLM-as-judge.

The user always owns the model and the bill. aiexpect never proxies calls;
it talks straight to the provider the user configured. Providers:

* ``ollama:<model>``            local, free, no key   (native /api/chat)
* ``anthropic:<model>``         official ``anthropic`` SDK, ``ANTHROPIC_API_KEY``
* ``openai:<model>``            ``OPENAI_API_KEY``, api.openai.com
* ``openai-compatible:<model>@<base_url>``  any OpenAI-style server (vLLM, LM Studio, Groq...)

Verdicts are cached on disk keyed by (provider, model, prompt) so re-running a
suite costs nothing until the text or the rubric changes.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..config import settings


class JudgeError(RuntimeError):
    """Raised when no judge is configured or the judge call fails."""


@dataclass
class Verdict:
    score: float          # 0..1
    reason: str
    raw: Dict[str, Any]
    cached: bool = False


JUDGE_SYSTEM = (
    "You are a strict, impartial evaluator used inside an automated test suite. "
    "You will be given an AI-generated response and an evaluation task. "
    "Judge only what is asked. Respond with a single JSON object and nothing else: "
    '{"score": <number from 0.0 to 1.0>, "reason": "<one or two sentences>"}. '
    "1.0 means the response fully satisfies the task, 0.0 means it clearly fails."
)

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_verdict(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = _JSON_RE.search(text)
        if not m:
            raise JudgeError(f"Judge did not return JSON: {text[:200]!r}") from None
        data = json.loads(m.group(0))
    if "score" not in data:
        raise JudgeError(f"Judge JSON has no 'score': {data!r}")
    data["score"] = max(0.0, min(1.0, float(data["score"])))
    data.setdefault("reason", "")
    return data


class Judge:
    provider = "base"
    model = ""

    def _complete(self, system: str, user: str) -> str:  # pragma: no cover - abstract
        raise NotImplementedError

    def judge(self, task: str) -> Verdict:
        key = None
        if settings.cache:
            key = hashlib.sha256(f"{self.provider}|{self.model}|{JUDGE_SYSTEM}|{task}".encode()).hexdigest()
            cached = _cache_get(key)
            if cached is not None:
                return Verdict(cached["score"], cached.get("reason", ""), cached, cached=True)
        text = self._complete(JUDGE_SYSTEM, task)
        data = _parse_verdict(text)
        if key:
            _cache_put(key, data)
        return Verdict(data["score"], data["reason"], data)

    def describe(self) -> str:
        return f"{self.provider}:{self.model}"


def _cache_path(key: str) -> str:
    return os.path.join(settings.cache_dir, key[:2], key + ".json")


def _cache_get(key: str) -> Optional[Dict[str, Any]]:
    p = _cache_path(key)
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _cache_put(key: str, data: Dict[str, Any]) -> None:
    p = _cache_path(key)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f)


def _post_json(url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
    timeout = settings.judge_timeout if timeout is None else timeout
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:500]
        raise JudgeError(f"{url} returned HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        if isinstance(e.reason, socket.timeout):
            raise JudgeError(_timeout_msg(url, timeout)) from e
        raise JudgeError(f"Could not reach {url}: {e.reason}") from e
    except (socket.timeout, TimeoutError) as e:
        raise JudgeError(_timeout_msg(url, timeout)) from e


def _timeout_msg(url: str, timeout: float) -> str:
    return (
        f"Judge call to {url} timed out after {timeout:.0f}s. If this is a local model, it is probably "
        "too big for this machine's RAM (an 8B model needs ~6 GB free; try `ollama pull llama3.2` or "
        "`qwen2.5:3b`). Raise the limit with AIEXPECT_JUDGE_TIMEOUT=600 if you just need more time."
    )


class OllamaJudge(Judge):
    provider = "ollama"

    def __init__(self, model: str = "llama3.2", host: Optional[str] = None) -> None:
        self.model = model
        self.host = (host or settings.ollama_host).rstrip("/")

    def _complete(self, system: str, user: str) -> str:
        data = _post_json(
            f"{self.host}/api/chat",
            {
                "model": self.model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "format": "json",
                "stream": False,
                "options": {"temperature": 0},
            },
        )
        return data["message"]["content"]


class OpenAICompatibleJudge(Judge):
    provider = "openai-compatible"

    def __init__(self, model: str, base_url: str, api_key: Optional[str] = None) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _complete(self, system: str, user: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        data = _post_json(
            f"{self.base_url}/chat/completions",
            {
                "model": self.model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
            headers=headers,
        )
        return data["choices"][0]["message"]["content"]


class OpenAIJudge(OpenAICompatibleJudge):
    provider = "openai"

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise JudgeError("OPENAI_API_KEY is not set")
        super().__init__(model, os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"), key)


_VERDICT_SCHEMA = {
    "type": "object",
    "properties": {"score": {"type": "number"}, "reason": {"type": "string"}},
    "required": ["score", "reason"],
    "additionalProperties": False,
}


class AnthropicJudge(Judge):
    provider = "anthropic"

    def __init__(self, model: str = "claude-opus-5") -> None:
        try:
            import anthropic  # type: ignore
        except ImportError as e:
            raise JudgeError("Install the Anthropic SDK: pip install 'aiexpect[anthropic]'") from e
        self.model = model
        self._client = anthropic.Anthropic()
        self._anthropic = anthropic

    def _complete(self, system: str, user: str) -> str:
        a = self._anthropic
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user}],
                # Judging is a short classification task: low effort keeps it cheap and fast.
                output_config={
                    "effort": "low",
                    "format": {"type": "json_schema", "schema": _VERDICT_SCHEMA},
                },
            )
        except a.AuthenticationError as e:
            raise JudgeError("Anthropic authentication failed: set ANTHROPIC_API_KEY") from e
        except a.RateLimitError as e:
            raise JudgeError("Anthropic rate limit hit; retry later") from e
        except a.APIStatusError as e:
            raise JudgeError(f"Anthropic API error {e.status_code}: {e.message}") from e
        except a.APIConnectionError as e:
            raise JudgeError(f"Could not reach Anthropic API: {e}") from e
        if response.stop_reason == "refusal":
            raise JudgeError("Anthropic judge refused to evaluate this content")
        return next(b.text for b in response.content if b.type == "text")


_judge: Optional[Judge] = None
_resolved = False


def reset() -> None:
    global _judge, _resolved
    _judge = None
    _resolved = False


def from_spec(spec: str) -> Judge:
    """Build a judge from ``provider:model[@base_url]``."""
    if ":" not in spec:
        raise JudgeError(f"Judge spec must look like 'provider:model', got {spec!r}")
    provider, rest = spec.split(":", 1)
    provider = provider.strip().lower()
    if provider == "ollama":
        return OllamaJudge(rest or "llama3.2")
    if provider == "anthropic":
        return AnthropicJudge(rest or "claude-opus-5")
    if provider == "openai":
        return OpenAIJudge(rest or "gpt-4o-mini")
    if provider in ("openai-compatible", "compat"):
        if "@" not in rest:
            raise JudgeError("openai-compatible spec needs '<model>@<base_url>'")
        model, base_url = rest.rsplit("@", 1)
        return OpenAICompatibleJudge(model, base_url, os.environ.get("OPENAI_API_KEY"))
    raise JudgeError(f"Unknown judge provider {provider!r}")


def _ollama_reachable() -> bool:
    try:
        with urllib.request.urlopen(settings.ollama_host + "/api/tags", timeout=1.5) as resp:
            data = json.loads(resp.read().decode())
            return bool(data.get("models"))
    except Exception:
        return False


def _ollama_first_model() -> str:
    with urllib.request.urlopen(settings.ollama_host + "/api/tags", timeout=1.5) as resp:
        data = json.loads(resp.read().decode())
        return data["models"][0]["name"]


def get_judge() -> Judge:
    """Return the configured judge, auto-detecting one if none was set.

    Order: explicit ``configure(judge=...)`` / ``AIEXPECT_JUDGE`` -> ANTHROPIC_API_KEY
    -> OPENAI_API_KEY -> a running Ollama with at least one model.
    """
    global _judge, _resolved
    if _resolved and _judge is not None:
        return _judge

    if settings.judge:
        _judge = from_spec(settings.judge)
    elif os.environ.get("ANTHROPIC_API_KEY"):
        try:
            _judge = AnthropicJudge()
        except JudgeError:
            _judge = None
    if _judge is None and os.environ.get("OPENAI_API_KEY"):
        _judge = OpenAIJudge()
    if _judge is None and _ollama_reachable():
        _judge = OllamaJudge(_ollama_first_model())
    if _judge is None:
        raise JudgeError(
            "This assertion needs an LLM judge and none is configured. Options:\n"
            "  - run Ollama locally (free):  ollama pull llama3.2  then  AIEXPECT_JUDGE=ollama:llama3.2\n"
            "  - export ANTHROPIC_API_KEY (pip install 'aiexpect[anthropic]')\n"
            "  - export OPENAI_API_KEY\n"
            "  - or in conftest.py: aiexpect.configure(judge='openai-compatible:<model>@<base_url>')"
        )
    _resolved = True
    return _judge
