# Choosing a judge (and whether you need one)

Tier 3 assertions (`to_be_grounded_in`, `to_answer`, `to_have_tone`, `to_satisfy`,
`to_be_consistent_with`, and judge-escalated `probes.check`) send the text to an LLM you run or pay for.
This page answers the question everyone asks first: **is a free local model good enough?**

## Measured: free 3B judge vs the keyword answer keys

Setup: the built-in hallucination probe pack (22 questions), each with a correct reply and a
fabricated reply (44 judgements). Judge: `ollama:llama3.2` (3B, 2 GB) on an 8 GB M1 MacBook Air,
temperature 0, JSON output. Ground truth: the probe's own keyword answer key.

| | Correct verdicts | Wall time |
|---|---|---|
| Tier 1 keyword key (free, no model) | 44 / 44 | < 0.1 s |
| Tier 3 `ollama:llama3.2` (free, local) | 43 / 44 | 82 s (~1.9 s per judgement) |

The single miss: the judge accepted *"The bricks are heavier because bricks are denser than feathers"*
as a correct answer to "which is heavier, a pound of feathers or a pound of bricks?" — a plausible-sounding
explanation beat the arithmetic. Every false-premise and true-premise probe was judged correctly, and every
judge reason was readable and specific (see the report).

Takeaways:

- For the probe pack, **Tier 1 alone is enough** and instantaneous; use the judge when your bot paraphrases
  corrections in ways the keyword key does not anticipate.
- A 3B local model is a **usable groundedness/tone/relevance judge** for CI. It will occasionally be
  talked into a confident wrong answer; keep `judge_threshold` at 0.7 and let `@consistent` absorb noise.
- Bigger models are better judges but must fit in RAM: an 8B model on an 8 GB laptop swapped to
  0.05 tokens/s in our test, which is why the default judge timeout is 300 s and the error message
  suggests a smaller model.

## Recommended setups

| Situation | Judge | Notes |
|---|---|---|
| Laptop, 8 GB RAM, free | `ollama:llama3.2` or `ollama:qwen2.5:3b` | ~2 s per judgement |
| Workstation, 16 GB+, free | `ollama:llama3.1` or `ollama:qwen2.5:7b` | noticeably better on nuance |
| CI runner, no GPU | Tier 1 + 2 only, or a cloud judge with the cache committed | judge cache makes reruns free |
| Best quality | `anthropic:claude-opus-5` (low effort) or `anthropic:claude-haiku-4-5` for cost | needs `ANTHROPIC_API_KEY` |
| Existing OpenAI-style server (vLLM, LM Studio, Groq) | `openai-compatible:<model>@<base_url>` | |

Settings: `AIEXPECT_JUDGE`, `AIEXPECT_JUDGE_THRESHOLD` (default 0.7), `AIEXPECT_JUDGE_TIMEOUT` (default 300 s),
`AIEXPECT_CACHE=0` to disable the verdict cache.

## Reproduce

The script that produced the table is `scripts/judge_agreement.py`.
Run it with any judge: `AIEXPECT_JUDGE=anthropic:claude-haiku-4-5 python scripts/judge_agreement.py`.
Contributions of results for other models are welcome (issue #5).
