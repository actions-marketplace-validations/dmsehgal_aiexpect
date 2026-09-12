# Changelog

## 0.1.0 (unreleased)

- First release. `expect()` chain with Tier 1 rules, Tier 2 semantic similarity
  (sentence-transformers or zero-dependency lexical fallback), Tier 3 LLM judge
  (Ollama, Anthropic, OpenAI, OpenAI-compatible) with on-disk verdict cache.
- `@consistent(samples, min_pass_rate)` for non-deterministic tests.
- pytest plugin: auto-loaded, Trust Score terminal summary, HTML + JSON report,
  `--llmexpect-min-trust` CI gate.
- `llmexpect` CLI: `check`, `report`, `summary`, `judge`.
