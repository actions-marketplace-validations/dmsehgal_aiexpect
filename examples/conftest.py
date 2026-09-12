import pytest
from support_bot import SupportBot


@pytest.fixture
def bot():
    return SupportBot()
