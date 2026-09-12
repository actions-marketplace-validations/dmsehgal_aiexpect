"""Tier 1 helpers: deterministic checks that never need a model."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

# Conservative PII patterns. False negatives are preferable to noisy false positives
# in a test suite; users can add their own via to_not_match().
PII_PATTERNS: Dict[str, re.Pattern] = {
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "phone": re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def find_pii(text: str, kinds: Tuple[str, ...] = tuple(PII_PATTERNS)) -> List[Tuple[str, str]]:
    found: List[Tuple[str, str]] = []
    for kind in kinds:
        for m in PII_PATTERNS[kind].finditer(text):
            val = m.group(0)
            if kind == "credit_card":
                digits = re.sub(r"\D", "", val)
                if not (13 <= len(digits) <= 16 and _luhn_ok(digits)):
                    continue
            found.append((kind, val))
    return found


def extract_json(text: str) -> Any:
    """Parse JSON from text, tolerating ```json fences and surrounding prose."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # find the first balanced {...} or [...]
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        while start != -1:
            depth = 0
            for i in range(start, len(text)):
                if text[i] == opener:
                    depth += 1
                elif text[i] == closer:
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start : i + 1])
                        except json.JSONDecodeError:
                            break
            start = text.find(opener, start + 1)
    raise ValueError("no JSON object found in text")


def validate_schema(data: Any, schema: Any) -> List[str]:
    """Validate ``data`` against ``schema``.

    ``schema`` may be a JSON-Schema dict (uses ``jsonschema`` if installed, else a
    minimal built-in checker for type/required/properties), a pydantic model
    class, or a plain dict of {key: type}.
    Returns a list of error strings; empty means valid.
    """
    # pydantic model class
    if isinstance(schema, type) and hasattr(schema, "model_validate"):
        try:
            schema.model_validate(data)  # type: ignore[attr-defined]
            return []
        except Exception as e:  # pydantic.ValidationError
            return [str(e)]
    if isinstance(schema, type) and hasattr(schema, "parse_obj"):  # pydantic v1
        try:
            schema.parse_obj(data)  # type: ignore[attr-defined]
            return []
        except Exception as e:
            return [str(e)]

    if isinstance(schema, dict) and ("type" in schema or "properties" in schema or "required" in schema):
        try:
            import jsonschema  # type: ignore

            v = jsonschema.Draft7Validator(schema)
            return [f"{'/'.join(str(p) for p in e.path) or '$'}: {e.message}" for e in v.iter_errors(data)]
        except ImportError:
            return _mini_schema(data, schema, "$")

    # {key: type} shorthand
    if isinstance(schema, dict):
        errors = []
        if not isinstance(data, dict):
            return [f"expected object, got {type(data).__name__}"]
        for k, t in schema.items():
            if k not in data:
                errors.append(f"missing key {k!r}")
            elif t is not Any and not isinstance(data[k], t):
                errors.append(f"{k!r}: expected {getattr(t, '__name__', t)}, got {type(data[k]).__name__}")
        return errors
    raise TypeError("schema must be a JSON-Schema dict, a pydantic model, or a {key: type} dict")


_TYPES = {
    "object": dict, "array": list, "string": str, "number": (int, float),
    "integer": int, "boolean": bool, "null": type(None),
}


def _mini_schema(data: Any, schema: Dict[str, Any], path: str) -> List[str]:
    errors: List[str] = []
    t = schema.get("type")
    if t:
        types = t if isinstance(t, list) else [t]
        ok = any(isinstance(data, _TYPES[x]) and not (x in ("number", "integer") and isinstance(data, bool)) for x in types if x in _TYPES)
        if not ok:
            errors.append(f"{path}: expected {t}, got {type(data).__name__}")
            return errors
    if isinstance(data, dict):
        for req in schema.get("required", []):
            if req not in data:
                errors.append(f"{path}: missing required {req!r}")
        for k, sub in schema.get("properties", {}).items():
            if k in data:
                errors.extend(_mini_schema(data[k], sub, f"{path}.{k}"))
    if isinstance(data, list) and "items" in schema:
        for i, item in enumerate(data):
            errors.extend(_mini_schema(item, schema["items"], f"{path}[{i}]"))
    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"{path}: {data!r} not in {schema['enum']}")
    return errors


REFUSAL_MARKERS = (
    "i can't", "i cannot", "i can not", "i'm unable", "i am unable", "i won't", "i will not",
    "not able to help", "unable to help", "can't help with", "cannot help with", "can't assist",
    "cannot assist", "i'm not able", "i am not able", "against my guidelines", "not something i can",
    "i must decline", "i have to decline", "not appropriate", "i'm sorry, but", "i am sorry, but",
)


def looks_like_refusal(text: str) -> bool:
    head = text.strip().lower()[:300]
    return any(m in head for m in REFUSAL_MARKERS)
