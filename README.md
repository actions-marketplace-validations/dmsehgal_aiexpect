# aiexpect

**Assertions for non-deterministic AI text. Drop into the tests you already have.**

```python
from aiexpect import expect

def test_refund_policy(bot):
    reply = bot.ask("What is your refund policy?")

    expect(reply).to_mean("you can return items within 30 days")   # semantic, no API key
    expect(reply).to_be_grounded_in(policy_doc)                    # no hallucination
    expect(reply).to_not_contain_pii().to_have_length(max=600)      # deterministic rules
```

Run `pytest` as usual. You get normal pass/fail **plus** a Trust Score and a self-contained HTML report with charts:

```
================================ aiexpect ================================
Trust Score: 87/100
  Accuracy 92 · Groundedness 85 · Relevance 90 · Safety 100 · Consistency 80 · Format 75
  41/46 checks passed (89%)
  report: /your/project/aiexpect-report.html
```

`pip install aiexpect` — zero dependencies, works offline out of the box.

---

## Why

Chatbot and LLM output changes every run. `assert reply == "..."` is useless, and most eval frameworks
want you to adopt a whole new platform. **aiexpect is just an assertion library**: it slots into pytest
(and soon Playwright/Cypress/Jest) next to your existing tests, and the results roll up into metrics a
non-ML person can read.

## Three tiers, free first

| Tier | Needs | Assertions |
|---|---|---|
| **1 · Rules** | nothing | `to_contain`, `to_not_contain`, `to_match`, `to_have_length`, `to_be_json`, `to_match_schema`, `to_not_contain_pii`, `to_be_one_of`, `to_refuse`, `to_satisfy_fn` |
| **2 · Semantic** | nothing (`pip install 'aiexpect[embeddings]'` for a real local embedding model) | `to_mean`, `to_not_mean`, `to_be_similar_to`, `to_be_relevant_to` |
| **3 · LLM judge** | any model **you** run or pay for: Ollama (free, local), Anthropic, OpenAI, or any OpenAI-compatible server | `to_be_grounded_in`, `to_answer`, `to_have_tone`, `to_satisfy(rubric)`, `to_be_consistent_with`, `to_refuse` (escalation) |

aiexpect never proxies your traffic. You bring the key; you own the bill. Judge verdicts are cached on disk
so re-running an unchanged suite costs nothing.

### Configure a judge (only needed for Tier 3)

```bash
# free, local
ollama pull llama3.1
export AIEXPECT_JUDGE=ollama:llama3.1

# or a cloud model
export ANTHROPIC_API_KEY=...            # auto-detected, uses claude-opus-5 at low effort
export AIEXPECT_JUDGE=anthropic:claude-haiku-4-5   # cheaper
export AIEXPECT_JUDGE=openai:gpt-4o-mini
export AIEXPECT_JUDGE=openai-compatible:qwen2.5@http://localhost:8000/v1   # vLLM, LM Studio, Groq...
```

or in `conftest.py`:

```python
import aiexpect
aiexpect.configure(judge="ollama:llama3.1", judge_threshold=0.7)
```

## Flaky by nature? Measure it.

```python
import aiexpect

@aiexpect.consistent(samples=5, min_pass_rate=0.8)
def test_greeting(bot):
    expect(bot.ask("hi")).to_have_tone("friendly")
```

Runs the body 5 times and passes on the pass-rate, not a single coin flip. Feeds the **Consistency** sub-score.

## The report

`pytest` writes `aiexpect-report.html` (and `.json`) every run:

- **Trust Score** (0–100) = mean of six plain-English sub-scores: Accuracy, Groundedness, Relevance, Safety, Consistency, Format
- pass rate per assertion type, score distribution, per-test table
- every check with the judge's reason, expandable, filterable (failed only / LLM-judged)
- single file, no CDN, light and dark mode, colour-blind-safe palette

CI gate: `pytest --aiexpect-min-trust=80` fails the run when the Trust Score drops below 80.

## CLI

```bash
aiexpect check "Return within 30 days" --contain "30 days" --no-pii --mean "30-day returns"
aiexpect report aiexpect-report.json -o report.html
aiexpect summary aiexpect-report.json --min-trust 80
aiexpect judge     # which judge would be used?
```

## Soft mode

```python
e = expect(reply, soft=True).to_contain("30 days").to_not_contain_pii().to_be_json()
e.verify()   # raises once with every failure listed
```

## Roadmap

- [ ] TypeScript port with Jest/Vitest matchers, Playwright fixture, Cypress commands
- [ ] Semantic snapshot testing (`to_match_snapshot()` diffed by meaning)
- [ ] Hallucination probe pack (false-premise, self-contradiction)
- [ ] GitHub Action with PR comment + badge
- [ ] Trend chart across runs

## Contributing

`uv venv && uv pip install -e ".[dev]" && pytest`. The test suite is fully offline (fake judge, lexical embeddings).
Adapters for other frameworks are the easiest first contribution — see `docs/`.

MIT © Deep Sehgal
