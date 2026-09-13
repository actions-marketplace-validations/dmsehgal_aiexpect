"""Verify dynamic text on a real web page with Playwright + aiexpect.

    pip install aiexpect pytest-playwright && playwright install chromium
    pytest examples/playwright -v

Wikipedia search is used because it is public, stable and has no bot-check.
Swap the URL and selectors for your own chat widget or results page.
"""
from aiexpect import expect

SEARCH = "https://en.wikipedia.org/w/index.php?fulltext=1&search="


def test_search_snippet_is_relevant(page):
    page.goto(SEARCH + "python+testing+framework")
    snippet = page.locator(".mw-search-result .searchresult").first.inner_text()

    # The text changes as Wikipedia is edited: assert on meaning, not exact words.
    expect(snippet).to_be_relevant_to("software testing framework")
    expect(snippet).to_contain_any("test", "testing").to_have_length(max=600)
    expect(snippet).to_not_contain_pii()
