# Writing an adapter

aiexpect's core is framework-agnostic: `expect(text)` records `CheckResult`s into
`aiexpect.collector` and raises `AssertionError` on failure. An adapter only has to

1. get the AI text out of the framework (a fixture, a page locator, an HTTP response),
2. call `expect(...)`,
3. at the end of the run, call `aiexpect.report.write_json(path, collector.results())`
   and `render_html(build_payload(...))`.

The pytest plugin (`src/aiexpect/pytest_plugin.py`, ~90 lines) is the reference adapter.
Wanted next: Robot Framework keywords, behave/pytest-bdd steps, a Playwright-Python fixture.
The TypeScript port will bring Jest/Vitest matchers, Playwright and Cypress commands.
