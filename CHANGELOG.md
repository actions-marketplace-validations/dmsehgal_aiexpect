# Changelog

## 0.2.0

- `to_match_snapshot()`: semantic snapshot testing (`--aiexpect-update-snapshots`,
  `--aiexpect-snapshot-mode=strict` for CI).
- Trust Score trend chart across runs (`.aiexpect_history.jsonl`, `--aiexpect-history`).
- `aiexpect.probes`: 22-question hallucination probe pack (false premise, true premise, factual)
  with `probes.check()` and `probes.run()`.
- All file I/O is explicit UTF-8 (fixes Windows).
- README with report screenshots and a comparison table; CONTRIBUTING; issue templates.

## 0.1.0

- First release. `expect()` chain with Tier 1 rules, Tier 2 semantic similarity
  (sentence-transformers or zero-dependency lexical fallback), Tier 3 LLM judge
  (Ollama, Anthropic, OpenAI, OpenAI-compatible) with on-disk verdict cache.
- `@consistent(samples, min_pass_rate)` for non-deterministic tests.
- pytest plugin: auto-loaded, Trust Score terminal summary, HTML + JSON report,
  `--aiexpect-min-trust` CI gate.
- `aiexpect` CLI: `check`, `report`, `summary`, `judge`.
