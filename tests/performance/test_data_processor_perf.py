"""Performance benchmarks for DividendDataProcessor CSV loading and filtering."""

from __future__ import annotations

import tracemalloc
from pathlib import Path

import pandas as pd
import pytest
from app.utils.dividend_calculator import DividendCalculator

from .conftest import (
    _GROWTH_RATE,
    _MAX_FILTER_1K_SEC,
    _SCALE_ROWS,
    _TICKERS_SMALL,
    _build_tsv_file,
)


@pytest.mark.benchmark
class TestDataProcessorPerformance:
    """Benchmarks for CSV loading and DataFrame filtering in DividendDataProcessor.

    Fixtures use ``tmp_path`` so every test gets a real, but temporary, file.
    """

    # -----------------------------------------------------------------------
    # Load from disk
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize("n_rows", _SCALE_ROWS, ids=[f"{n}rows" for n in _SCALE_ROWS])
    def test_load_and_clean_data(self, benchmark: pytest.fixture, tmp_path: Path, n_rows: int) -> None:
        """Benchmark: full load + clean cycle for portfolios of different sizes.

        Args:
            benchmark: pytest-benchmark fixture.
            tmp_path: pytest temporary directory (function-scoped).
            n_rows: Number of portfolio rows in the test TSV file.
        """
        from app.data_processor import DividendDataProcessor

        file_path = _build_tsv_file(tmp_path, n_rows)

        def _load() -> DividendDataProcessor:
            return DividendDataProcessor(str(file_path))

        processor = benchmark.pedantic(_load, rounds=5, warmup_rounds=2)
        assert not processor.df.empty
        assert len(processor.df) == n_rows
        assert benchmark.stats["mean"] < _MAX_FILTER_1K_SEC

    # -----------------------------------------------------------------------
    # filter_data
    # -----------------------------------------------------------------------

    def test_filter_single_ticker(self, benchmark: pytest.fixture, tmp_path: Path) -> None:
        """Benchmark: filtering a 1 000-row portfolio down to a single ticker.

        Args:
            benchmark: pytest-benchmark fixture.
            tmp_path: pytest temporary directory.
        """
        from app.data_processor import DividendDataProcessor

        file_path = _build_tsv_file(tmp_path, 1_000)
        processor = DividendDataProcessor(str(file_path))

        result = benchmark(processor.filter_data, ["AAPL.US"])
        assert not result.empty

    def test_filter_all_tickers(self, benchmark: pytest.fixture, tmp_path: Path) -> None:
        """Benchmark: filtering passes through the full portfolio unchanged.

        Args:
            benchmark: pytest-benchmark fixture.
            tmp_path: pytest temporary directory.
        """
        from app.data_processor import DividendDataProcessor

        file_path = _build_tsv_file(tmp_path, 1_000)
        processor = DividendDataProcessor(str(file_path))

        result = benchmark(processor.filter_data, _TICKERS_SMALL)
        assert not result.empty

    def test_filter_empty_selection(self, benchmark: pytest.fixture, tmp_path: Path) -> None:
        """Benchmark: filter with empty list returns immediately.

        Args:
            benchmark: pytest-benchmark fixture.
            tmp_path: pytest temporary directory.
        """
        from app.data_processor import DividendDataProcessor

        file_path = _build_tsv_file(tmp_path, 500)
        processor = DividendDataProcessor(str(file_path))

        result = benchmark(processor.filter_data, [])
        assert result.empty

    # -----------------------------------------------------------------------
    # End-to-end pipeline (load → filter → project)
    # -----------------------------------------------------------------------

    def test_full_pipeline_500_rows(self, benchmark: pytest.fixture, tmp_path: Path) -> None:
        """Benchmark: full pipeline – load 500 rows, filter, then project.

        Simulates one complete render cycle of the dashboard.

        Args:
            benchmark: pytest-benchmark fixture.
            tmp_path: pytest temporary directory.
        """
        from app.data_processor import DividendDataProcessor

        file_path = _build_tsv_file(tmp_path, 500)

        def _pipeline() -> pd.DataFrame:
            processor = DividendDataProcessor(str(file_path))
            filtered = processor.filter_data(["AAPL.US"])
            if filtered.empty:
                return filtered
            initial = filtered["Net Dividend"].iloc[0]
            return DividendCalculator.calculate_projections(initial, _GROWTH_RATE, 20)

        result = benchmark.pedantic(_pipeline, rounds=5, warmup_rounds=2)
        assert result is not None

    # -----------------------------------------------------------------------
    # Memory – tracemalloc
    # -----------------------------------------------------------------------

    def test_load_memory_footprint_1000_rows(self, tmp_path: Path) -> None:
        """Verify loading 1 000 rows allocates < 4 MiB of Python objects.

        Args:
            tmp_path: pytest temporary directory.
        """
        from app.data_processor import DividendDataProcessor

        file_path = _build_tsv_file(tmp_path, 1_000)

        tracemalloc.start()
        DividendDataProcessor(str(file_path))
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mib = peak_bytes / (1024**2)
        assert peak_mib < 4, f"Loading 1 000 rows allocated {peak_mib:.2f} MiB – expected < 4 MiB"
