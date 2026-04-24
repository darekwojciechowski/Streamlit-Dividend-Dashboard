# E2E Tests

End-to-end Playwright suite for the Streamlit Dividend Dashboard. Runs
the real app in a real browser and exercises the full user journey
(navigation, controls, chart rendering, accessibility, responsive layout).

## Quickstart

Two commands to run the suite from a fresh clone:

```bash
poetry run streamlit run main.py           # terminal 1 — keep running
poetry run pytest tests/e2e/ -m e2e        # terminal 2 — runs the suite
```

The session-autouse fixture probes `http://localhost:8501` once; if the
server is unreachable the suite is skipped (not failed).

First run also needs Playwright browsers:

```bash
poetry run playwright install chromium firefox
```

## Marker matrix

Every test is tagged so you can slice the suite by intent:

| Marker        | Scope                                                 |
|---------------|-------------------------------------------------------|
| `e2e`         | The whole suite (umbrella).                           |
| `smoke`       | Fast read-only checks — headings, tiles render.       |
| `critical`    | Must-not-regress financial / a11y assertions.         |
| `regression`  | Guards a previously-broken invariant.                 |
| `a11y`        | Accessibility — axe-core + keyboard navigation.       |
| `responsive`  | Mobile / tablet viewport rendering.                   |
| `charts`      | Plotly + Nivo chart element presence.                 |

Examples:

```bash
poetry run pytest tests/e2e/ -m smoke            # < 10s, pre-commit gate
poetry run pytest tests/e2e/ -m a11y             # axe + keyboard suite
poetry run pytest tests/e2e/ -m "critical and regression"  # release gate
poetry run pytest tests/e2e/ -m "e2e and not slow"         # dev loop
```

## Cross-browser

```bash
poetry run pytest tests/e2e/ --browser chromium
poetry run pytest tests/e2e/ --browser firefox
```

CI runs both as a matrix job; artifacts are uploaded per browser
(`test-results-e2e-chromium`, `test-results-e2e-firefox`).

## Debugging

| Goal                          | Command                                             |
|-------------------------------|-----------------------------------------------------|
| Watch the browser             | `HEADED=1 poetry run pytest tests/e2e/`             |
| Step through interactively    | `PWDEBUG=1 poetry run pytest tests/e2e/`            |
| Slow-motion replay            | `PW_SLOWMO_MS=250 HEADED=1 poetry run pytest ...`   |
| Record video of every test    | `PWDEBUG=1 ...` (video written to `test-results-e2e/video/`) |
| Open trace on failure         | `poetry run playwright show-trace test-results-e2e/.../trace.zip` |

## Architecture

```
tests/e2e/
├── conftest.py              # session fixtures, Playwright contract hooks
├── constants.py             # BASE_URL, timeouts, viewports, headings
├── helpers/
│   ├── streamlit.py         # wait_streamlit_idle, wait_for_rerun
│   └── parsing.py           # parse_currency
├── pages/                   # Page Object Model — one file per section
│   ├── base_section.py      # shared __init__ + wait helpers
│   ├── dashboard_page.py
│   ├── growth_calculator.py
│   └── drip_section.py
└── test_*.py                # assertions only — no Playwright API calls
```

Flow on any test:

```
conftest fixtures → POM actions → POM locators → playwright.expect assertions
```

Tests never call `page.locator(...)` directly — locators live in POMs. If
a selector breaks, there's exactly one place to fix it.

## Conventions

- **Web-first assertions only** — `expect(locator).to_be_visible()`, not
  `assert locator.is_visible()`. Playwright auto-retries the first; the
  second snapshots once and flakes.
- **No hardcoded sleeps** — use `BaseSection._wait_for_rerun()` after any
  widget change. `page.wait_for_timeout(...)` is banned in POMs.
- **Stable selectors** — prefer `data-testid` and ARIA roles over CSS
  classes. `.tiles-container` and `.metric-card` are already migrated.
- **AAA per test** — Arrange, Act, Assert. Separate with a blank line
  when the test is longer than 5 lines.

## CI artifacts

On failure each browser job uploads:

- `test-results-e2e-<browser>/` — Playwright traces + screenshots.
- `report.html` — self-contained pytest-html report with embedded
  failure screenshots (linked from the job summary).
- `/tmp/streamlit.log` — server log (last 20 KB).

A run passes the flake floor if `pytest tests/e2e/ -m e2e` green-passes
five times back-to-back.
