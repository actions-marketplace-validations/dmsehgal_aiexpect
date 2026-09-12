# Contributing to aiexpect

Thanks for helping. The bar is low on purpose: small, focused PRs with a test.

## Setup

```bash
uv venv && uv pip install -e ".[dev]"
pytest                 # fully offline: fake judge + lexical embeddings
ruff check src tests
```

## Good first contributions

- **A new assertion.** Add a method to `Expectation` in `src/aiexpect/expectation.py`, pick the right
  `category` (accuracy / groundedness / relevance / safety / consistency / format) and `tier`, add a test.
- **A probe pack.** Add `Probe` entries to `src/aiexpect/probes.py` with a keyword answer key, and a test that
  the reference answer passes its own key.
- **An adapter.** See `docs/adapters.md`. The pytest plugin is the reference implementation.
- **Judge provider.** Subclass `Judge` in `src/aiexpect/backends/judges.py`; register it in `from_spec`.

## Rules of the house

- Base install stays **zero-dependency** and must work offline. Anything heavier is an optional extra.
- aiexpect never proxies LLM calls or ships credentials; the user always owns the model and the bill.
- Every `open()` passes `encoding="utf-8"` (Windows CI will catch you otherwise).
- Python 3.9+ syntax only in `src/` (no `match`, no `X | Y` outside annotations).
- Keep the report a single self-contained HTML file with no CDN.

## Releasing (maintainers)

Bump `version` in `pyproject.toml` and `__version__` in `src/aiexpect/__init__.py`, update `CHANGELOG.md`,
then `gh release create vX.Y.Z`. Trusted publishing uploads to PyPI automatically.
