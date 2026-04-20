# Tests

Test suite for the Streamlit Dividend Dashboard. Uses [pytest](https://docs.pytest.org/) with
[hypothesis](https://hypothesis.readthedocs.io/) for property-based testing.

## Structure

```
tests/
├── conftest.py              # Shared fixtures (session, module, function scope)
├── unit/                    # Fast, isolated tests — no I/O, no external deps
│   ├── test_app_config.py
│   ├── test_color_manager.py
│   ├── test_data_processor.py
│   ├── test_dividend_calculator.py
│   └── test_error_handling.py
├── integration/             # Component interaction & file I/O tests
│   ├── test_color_generation_workflow.py
│   ├── test_data_processing_workflow.py
│   └── test_dividend_calculation_workflow.py
├── property_based/          # Generative tests via hypothesis
│   └── test_property_based.py
├── performance/             # Benchmark tests via pytest-benchmark
│   └── test_performance.py
└── e2e/                     # Browser-level tests via Playwright
    ├── conftest.py          # Playwright fixtures + live-server health check
    ├── pages/               # Page Object Model helpers
    │   ├── dashboard_page.py
    │   ├── drip_section.py
    │   └── growth_calculator.py
    ├── test_dashboard.py
    ├── test_accessibility.py
    ├── test_drip_calculator.py
    ├── test_growth_calculator.py
    ├── test_responsive.py
    └── test_ticker_filtering.py
```

## Running Tests

```bash
# Run all tests
poetry run pytest

# Run a specific layer
poetry run pytest tests/unit/
poetry run pytest tests/integration/
poetry run pytest tests/property_based/
poetry run pytest tests/performance/
poetry run pytest tests/e2e/

# Filter by marker
poetry run pytest -m unit
poetry run pytest -m "not slow"

# Show coverage (requires pytest-cov)
poetry run pytest --cov=app --cov-report=term-missing
```

## E2E Tests

#### Prerequisites (one-time)
```bash
poetry run playwright install chromium
```

#### Step 1 — Start the Streamlit app
E2E tests require a live server on `http://localhost:8501`. In a separate terminal:
```bash
# from the project root directory
poetry run streamlit run main.py
```
Tests skip automatically (via `pytest.skip`) when the server is unreachable.

#### Step 2 — Run E2E tests
```bash
# All E2E tests (headless by default)
poetry run pytest tests/e2e/

# Filter by marker
poetry run pytest -m e2e

# Headed mode (watch the browser)
poetry run pytest tests/e2e/ --headed

# Choose browser (chromium / firefox / webkit)
poetry run pytest tests/e2e/ --browser firefox

# Save screenshots and traces on failure
poetry run pytest tests/e2e/ --screenshot=only-on-failure --tracing=retain-on-failure

# Retry flaky tests (up to 2 retries)
poetry run pytest tests/e2e/ --reruns 2

# Single file
poetry run pytest tests/e2e/test_drip_calculator.py
```

## Markers

| Marker       | Description                                      |
|--------------|--------------------------------------------------|
| `unit`       | Fast, isolated, no I/O                           |
| `integration`| Component interaction and file I/O               |
| `e2e`        | Full user workflows                              |
| `slow`       | Takes > 1 second — skip with `-m "not slow"`    |
| `property`   | Property-based tests via hypothesis              |
| `benchmark`  | Performance benchmarks via pytest-benchmark      |

## Fixtures

All shared fixtures live in `conftest.py`.

| Fixture                   | Scope    | Description                                           |
|---------------------------|----------|-------------------------------------------------------|
| `test_data_dir`           | session  | Persistent temp directory for the whole session       |
| `sample_dividend_data`    | function | Clean `DataFrame` — 5 rows, 4 tickers                 |
| `sample_tsv_file`         | function | TSV file with raw `" USD"` / `"%"` suffixes           |
| `dashboard_page`          | function | Fresh Playwright page, navigated and fully rendered   |
| `dashboard_page_readonly` | class    | Shared page for read-only smoke tests (faster)        |
| `portfolio_tickers`       | session  | Ticker list read from the real CSV data file          |

## Conventions

- **Pattern:** Arrange → Act → Assert (AAA).
- **Naming:** `test_<unit>_<scenario>_<expected_outcome>`.
- **Isolation:** Each test is independent; no shared mutable state.
- **Mocking:** Use `pytest-mock` (`mocker`) or `unittest.mock.patch` for external deps.
- **File I/O:** Use the built-in `tmp_path` fixture — never write to the project tree.
