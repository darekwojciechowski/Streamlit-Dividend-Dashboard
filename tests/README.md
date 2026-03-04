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
└── property_based/          # Generative tests via hypothesis
│   └── test_property_based.py
└── performance/             # Benchmark tests via pytest-benchmark
    └── test_performance.py
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

# Filter by marker
poetry run pytest -m unit
poetry run pytest -m "not slow"

# Show coverage (requires pytest-cov)
poetry run pytest --cov=app --cov-report=term-missing
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

| Fixture                | Scope    | Description                                      |
|------------------------|----------|--------------------------------------------------|
| `test_data_dir`        | session  | Persistent temp directory for the whole session  |
| `sample_dividend_data` | function | Clean `DataFrame` — 5 rows, 4 tickers            |
| `sample_tsv_file`      | function | TSV file with raw `" USD"` / `"%"` suffixes      |

## Conventions

- **Pattern:** Arrange → Act → Assert (AAA).
- **Naming:** `test_<unit>_<scenario>_<expected_outcome>`.
- **Isolation:** Each test is independent; no shared mutable state.
- **Mocking:** Use `pytest-mock` (`mocker`) or `unittest.mock.patch` for external deps.
- **File I/O:** Use the built-in `tmp_path` fixture — never write to the project tree.
