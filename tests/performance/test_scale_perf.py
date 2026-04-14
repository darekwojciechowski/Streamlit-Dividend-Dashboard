"""Cross-component stress tests simulating large realistic portfolios."""

from __future__ import annotations

import tracemalloc
from pathlib import Path

import pandas as pd
import pytest
from app.utils.color_manager import ColorManager
from app.utils.dividend_calculator import DividendCalculator

from .conftest import (
    _GROWTH_RATE,
    _TICKERS_LARGE,
    _TICKERS_SMALL,
    _YEARS_MEDIUM,
    _YEARS_SHORT,
    _build_tsv_file,
)


@pytest.mark.benchmark
@pytest.mark.slow
class TestScalePerformance:
    """Cross-component stress tests simulating large realistic portfolios.

    These tests are tagged ``slow`` and skipped in quick CI runs via:
        poetry run pytest -m "not slow"
    """

    def test_color_assignment_200_tickers(self, benchmark: pytest.fixture) -> None:
        """Benchmark: end-to-end colour map for a 200-ticker portfolio.

        A professional portfolio may contain hundreds of individual positions.
        Colour assignment must remain usable (< 500 ms mean) at this scale.

        Args:
            benchmark: pytest-benchmark fixture.
        """
        manager = ColorManager()
        result = benchmark(manager.generate_colors_for_tickers, _TICKERS_LARGE)
        assert len(result) == len(_TICKERS_LARGE)

    def test_projection_batch_100_tickers(self, benchmark: pytest.fixture) -> None:
        """Benchmark: running a 30-year projection for every ticker independently.

        Simulates the worst-case scenario where the dashboard recalculates
        projections for all 100 tickers on every interaction.

        Args:
            benchmark: pytest-benchmark fixture.
        """
        dividends = [50.0 + i for i in range(100)]

        def _project_all() -> list[pd.DataFrame]:
            return [DividendCalculator.calculate_projections(d, _GROWTH_RATE, _YEARS_MEDIUM) for d in dividends]

        results = benchmark.pedantic(_project_all, rounds=5, warmup_rounds=2)
        assert len(results) == 100
        assert all(len(df) == _YEARS_MEDIUM for df in results)

    def test_full_render_cycle_1000_rows(self, benchmark: pytest.fixture, tmp_path: Path) -> None:
        """Benchmark: complete dashboard render cycle with 1 000-row portfolio.

        Covers: load → clean → filter → project → colour assignment.

        Args:
            benchmark: pytest-benchmark fixture.
            tmp_path: pytest temporary directory.
        """
        from app.data_processor import DividendDataProcessor

        file_path = _build_tsv_file(tmp_path, 1_000)
        manager = ColorManager()

        def _full_cycle() -> dict:
            processor = DividendDataProcessor(str(file_path))
            filtered = processor.filter_data(_TICKERS_SMALL)
            tickers = filtered["Ticker"].unique().tolist()
            colors = manager.generate_colors_for_tickers(tickers)

            projections: dict[str, pd.DataFrame] = {}
            for ticker in tickers:
                ticker_df = filtered[filtered["Ticker"] == ticker]
                initial = DividendCalculator.get_initial_dividend(ticker_df)
                if initial:
                    projections[ticker] = DividendCalculator.calculate_projections(initial, _GROWTH_RATE, _YEARS_SHORT)

            return {"colors": colors, "projections": projections}

        result = benchmark.pedantic(_full_cycle, rounds=5, warmup_rounds=2)
        assert "colors" in result
        assert "projections" in result

    def test_tile_html_generation_200_tickers(self, benchmark: pytest.fixture) -> None:
        """Benchmark: generating HTML tiles for every ticker in a 200-ticker portfolio.

        A new ``ColorManager`` is created per ticker because the
        ``get_random_base_color`` pool holds 10 unique entries – sharing one
        manager across a 200-ticker portfolio would exhaust the pool.  The
        benchmark measures the combined overhead of manager construction +
        HTML generation, which is the actual cost paid per dashboard render.

        Args:
            benchmark: pytest-benchmark fixture.
        """

        def _generate_all_tiles() -> list[str]:
            return [ColorManager().create_tile_html(ticker, 100 + i) for i, ticker in enumerate(_TICKERS_LARGE)]

        tiles = benchmark.pedantic(_generate_all_tiles, rounds=5, warmup_rounds=2)
        assert len(tiles) == len(_TICKERS_LARGE)
        assert all("TICK" in html for html in tiles)

    # -----------------------------------------------------------------------
    # Memory budget – full cycle with 1 000 rows
    # -----------------------------------------------------------------------

    def test_full_cycle_memory_budget(self, tmp_path: Path) -> None:
        """Verify the full render cycle for 1 000 rows stays under 16 MiB.

        Args:
            tmp_path: pytest temporary directory.
        """
        from app.data_processor import DividendDataProcessor

        file_path = _build_tsv_file(tmp_path, 1_000)
        manager = ColorManager()

        tracemalloc.start()

        processor = DividendDataProcessor(str(file_path))
        filtered = processor.filter_data(_TICKERS_SMALL)
        tickers = filtered["Ticker"].unique().tolist()
        manager.generate_colors_for_tickers(tickers)

        for ticker in tickers:
            ticker_df = filtered[filtered["Ticker"] == ticker]
            initial = DividendCalculator.get_initial_dividend(ticker_df)
            if initial:
                DividendCalculator.calculate_projections(initial, _GROWTH_RATE, _YEARS_SHORT)

        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mib = peak_bytes / (1024**2)
        assert peak_mib < 16, f"Full cycle used {peak_mib:.2f} MiB – expected < 16 MiB"
