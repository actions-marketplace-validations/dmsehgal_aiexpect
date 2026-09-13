# Changelog

## 0.3.0

- GitHub Action (`uses: dmsehgal/aiexpect@v0.3.0`): Trust Score as a PR comment + job summary, optional gate.
- `aiexpect summary --markdown` for CI comments.
- Playwright example (`examples/playwright`) verifying dynamic search-result text on a real page.
- README: terminal demo GIF, report walkthrough GIF, Tier 2 negation caveat (measured).
- pytest summary prints the report path relative to the working directory.

## 0.2.2

- Judge timeouts are configurable (`AIEXPECT_JUDGE_TIMEOUT`, default 300 s) and surface as a clear
  `JudgeError` suggesting a smaller local model, instead of a raw traceback.
- Default Ollama recommendation is now `llama3.2` (2 GB) so it fits 8 GB laptops.
- `docs/judges.md`: measured agreement of a free 3B judge vs the probe answer keys (43/44), plus
  `scripts/judge_agreement.py` to reproduce with any judge.

## 0.2.1

- Packaging/metadata only: neutral wording in the README and probe docstring. No code changes.

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
