"""Performance benchmarks for DividendCalculator pure-math helpers."""

from __future__ import annotations

import tracemalloc

import pytest
from app.utils.dividend_calculator import DividendCalculator

from .conftest import (
    _GROWTH_RATE,
    _INITIAL_DIVIDEND,
    _MAX_PROJECTION_10Y_SEC,
    _MAX_PROJECTION_50Y_SEC,
    _YEARS_LONG,
    _YEARS_MEDIUM,
    _YEARS_SHORT,
)


@pytest.mark.benchmark
class TestDividendCalculatorPerformance:
    """Benchmarks for pure-math helpers in DividendCalculator.

    All methods under test are ``@staticmethod`` and have no I/O,
    so any regression is a pure algorithmic change.
    """

    # -----------------------------------------------------------------------
    # calculate_projections
    # -----------------------------------------------------------------------

    def test_projections_10_years(self, benchmark: pytest.fixture) -> None:
        """Benchmark: projection for 10-year horizon.

        Establishes the baseline latency for the shortest supported
        projection (dashboard default).

        Args:
            benchmark: pytest-benchmark fixture.
        """
        result = benchmark(
            DividendCalculator.calculate_projections,
            _INITIAL_DIVIDEND,
            _GROWTH_RATE,
            _YEARS_SHORT,
        )
        assert len(result) == _YEARS_SHORT
        assert benchmark.stats["mean"] < _MAX_PROJECTION_10Y_SEC

    def test_projections_30_years(self, benchmark: pytest.fixture) -> None:
        """Benchmark: projection for 30-year horizon (CAGR analysis).

        Args:
            benchmark: pytest-benchmark fixture.
        """
        result = benchmark(
            DividendCalculator.calculate_projections,
            _INITIAL_DIVIDEND,
            _GROWTH_RATE,
            _YEARS_MEDIUM,
        )
        assert len(result) == _YEARS_MEDIUM

    def test_projections_50_years(self, benchmark: pytest.fixture) -> None:
        """Benchmark: projection for 50-year horizon (extreme / retirement planning).

        Args:
            benchmark: pytest-benchmark fixture.
        """
        result = benchmark(
            DividendCalculator.calculate_projections,
            _INITIAL_DIVIDEND,
            _GROWTH_RATE,
            _YEARS_LONG,
        )
        assert len(result) == _YEARS_LONG
        assert benchmark.stats["mean"] < _MAX_PROJECTION_50Y_SEC

    @pytest.mark.parametrize(
        "growth_rate",
        [0.0, 1.0, 7.0, 15.0, -5.0],
        ids=["flat", "low", "moderate", "high", "negative"],
    )
    def test_projections_various_growth_rates(self, benchmark: pytest.fixture, growth_rate: float) -> None:
        """Benchmark: projection latency is rate-independent.

        Growth rate changes only the values, not the algorithmic complexity.
        All rates should complete in comparable time.

        Args:
            benchmark: pytest-benchmark fixture.
            growth_rate: Annual growth rate percentage to test.
        """
        result = benchmark(
            DividendCalculator.calculate_projections,
            _INITIAL_DIVIDEND,
            growth_rate,
            _YEARS_MEDIUM,
        )
        assert len(result) == _YEARS_MEDIUM

    # -----------------------------------------------------------------------
    # calculate_growth_info
    # -----------------------------------------------------------------------

    def test_growth_info_calculation(self, benchmark: pytest.fixture) -> None:
        """Benchmark: growth statistics summary for 30-year horizon.

        Args:
            benchmark: pytest-benchmark fixture.
        """
        result = benchmark(
            DividendCalculator.calculate_growth_info,
            _INITIAL_DIVIDEND,
            _GROWTH_RATE,
            _YEARS_MEDIUM,
        )
        assert "final_dividend" in result
        assert "total_growth_pct" in result

    @pytest.mark.parametrize("years", [1, 10, 30, 50], ids=["1y", "10y", "30y", "50y"])
    def test_growth_info_scaling_with_years(self, benchmark: pytest.fixture, years: int) -> None:
        """Benchmark: growth_info is O(1) regardless of year count.

        ``calculate_growth_info`` uses a single power-law formula – execution
        time must not grow proportionally with ``years``.

        Args:
            benchmark: pytest-benchmark fixture.
            years: Projection horizon in years.
        """
        result = benchmark(
            DividendCalculator.calculate_growth_info,
            _INITIAL_DIVIDEND,
            _GROWTH_RATE,
            years,
        )
        assert result["years"] == years

    # -----------------------------------------------------------------------
    # get_currency_symbol
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        "ticker",
        ["AAPL.US", "PKO.PL", "SAP.EU", "UNKNOWN.XX", "NODOT"],
        ids=["us", "pl", "eu", "unknown", "no-dot"],
    )
    def test_currency_symbol_lookup(self, benchmark: pytest.fixture, ticker: str) -> None:
        """Benchmark: currency symbol inference is effectively O(1).

        Args:
            benchmark: pytest-benchmark fixture.
            ticker: Ticker string including optional country suffix.
        """
        result = benchmark(DividendCalculator.get_currency_symbol, ticker)
        assert isinstance(result, str)
        assert len(result) >= 1

    # -----------------------------------------------------------------------
    # Memory – tracemalloc (non-benchmark assertions)
    # -----------------------------------------------------------------------

    def test_projections_memory_footprint_50_years(self) -> None:
        """Verify 50-year projection allocates < 256 KiB of Python objects.

        A single projection DataFrame should never approach megabyte territory
        regardless of the year count.
        """
        tracemalloc.start()
        DividendCalculator.calculate_projections(_INITIAL_DIVIDEND, _GROWTH_RATE, _YEARS_LONG)
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_kib = peak_bytes / 1024
        assert peak_kib < 256, f"Projection allocated {peak_kib:.1f} KiB – expected < 256 KiB"
