import pytest

import aiexpect
from aiexpect.backends import judges


class FakeJudge(judges.Judge):
    """Deterministic judge for offline tests. Scores by keyword in the task."""

    provider = "fake"
    model = "keyword"

    def _complete(self, system, user):
        # Only look at the response under test, not the instructions in the task.
        low = user.lower().split("response:")[-1]
        if "unicorn" in low:
            return '{"score": 0.1, "reason": "contains unsupported claim about unicorns"}'
        if "grumpy" in low:
            return '{"score": 0.2, "reason": "tone is rude"}'
        return '{"score": 0.95, "reason": "looks good"}'


@pytest.fixture(autouse=True)
def _offline_config(tmp_path, monkeypatch):
    # Force the zero-dependency backends and a fake judge so the suite never hits the network.
    monkeypatch.setattr(judges, "_judge", FakeJudge())
    monkeypatch.setattr(judges, "_resolved", True)
    aiexpect.settings.embeddings = "lexical"
    aiexpect.settings.cache_dir = str(tmp_path / "cache")
    from aiexpect.backends import embeddings
    embeddings.reset()
    yield
