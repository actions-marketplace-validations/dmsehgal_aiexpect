# Security

Please report vulnerabilities privately through GitHub's
[private vulnerability reporting](https://github.com/dmsehgal/aiexpect/security/advisories/new)
rather than in a public issue. You will get a response within a week.

What aiexpect does with your data: assertions run locally. Only Tier 3 checks send the text under test
to the LLM provider **you** configured (Ollama, Anthropic, OpenAI, or your own OpenAI-compatible server).
Nothing is sent anywhere else, and no credentials are stored by aiexpect; provider keys are read from
your environment at call time. Judge verdicts are cached in `.aiexpect_cache/` in your project — add it to
`.gitignore` if the text under test is sensitive.
