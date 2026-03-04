"""Performance benchmarks for the Streamlit Dividend Dashboard.

This module contains pytest-benchmark performance tests that guard against
regressions in throughput-critical paths: data loading and filtering,
dividend projection calculations, and color assignment for portfolio tiles.

Test organisation:
    - TestDividendCalculatorPerformance: Pure-math benchmarks (projections, growth).
    - TestDataProcessorPerformance: I/O benchmarks (load, filter, scale).
    - TestColorManagerPerformance: Color generation and tile HTML benchmarks.
    - TestColorUtilsPerformance: Module-level color helper benchmarks.
    - TestScalePerformance: Cross-component stress tests with large portfolios.

Benchmark configuration (per-group defaults):
    - min_rounds = 20 for fast functions, 5 for heavy I/O.
    - warmup_rounds = 3 to eliminate JIT / first-import overhead.
    - timer = time.perf_counter (highest-resolution wall clock).

All performance budgets are intentionally loose so that they pass on any
CI machine.  The key goal is *regression detection* through benchmark
history, not absolute latency enforcement.

Usage:
    # Run only performance benchmarks
    poetry run pytest tests/performance/ -v

    # Compare against a saved baseline
    poetry run pytest tests/performance/ --benchmark-compare

    # Save results as new baseline
    poetry run pytest tests/performance/ --benchmark-save=baseline
"""

from __future__ import annotations

import tracemalloc
from pathlib import Path

import pandas as pd
import pytest

from app.utils.color_manager import (
    ColorManager,
    adjust_gradient,
    apply_wcag_ui_standards,
    determine_text_color_for_dropdown,
    hex_to_rgba,
    rgb_to_hex,
)
from app.utils.dividend_calculator import DividendCalculator

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Projection inputs
_INITIAL_DIVIDEND = 100.0
_GROWTH_RATE = 7.0
_YEARS_SHORT = 10
_YEARS_MEDIUM = 30
_YEARS_LONG = 50

# Benchmark time budgets (seconds) – very conservative for CI robustness.
_MAX_PROJECTION_10Y_SEC = 0.01
_MAX_PROJECTION_50Y_SEC = 0.05
_MAX_FILTER_1K_SEC = 0.1
_MAX_COLOR_GEN_100_SEC = 0.5

# Ticker pools
_TICKERS_SMALL: list[str] = ["AAPL.US", "MSFT.US", "PKO.PL", "SAP.EU"]
_TICKERS_MEDIUM: list[str] = [f"TICK{i:03d}.US" for i in range(50)]
_TICKERS_LARGE: list[str] = [f"TICK{i:03d}.US" for i in range(200)]

# Portfolio scale sizes for parametrised benchmarks
_SCALE_ROWS = [100, 500, 1_000]

# Hex / RGB colour samples for utility benchmarks
_SAMPLE_HEX_COLORS = [
    "#FF6B6B",
    "#4ECDC4",
    "#95E1D3",
    "#FFD93D",
    "#A8E6CE",
    "#000000",
    "#FFFFFF",
    "#8A2BE2",
]
_SAMPLE_RGB_COLORS = [
    "rgb(255, 107, 107)",
    "rgb(78, 205, 196)",
    "rgb(149, 225, 211)",
    "rgb(255, 217, 61)",
    "rgb(0, 0, 0)",
]


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------


def _build_portfolio_df(n_rows: int, tickers: list[str] | None = None) -> pd.DataFrame:
    """Return a synthetic portfolio DataFrame of *n_rows* rows.

    Args:
        n_rows: Number of rows to generate.
        tickers: Ticker pool to cycle through.  Defaults to ``_TICKERS_SMALL``.

    Returns:
        A ``pd.DataFrame`` with columns matching ``REQUIRED_COLUMNS`` and
        pre-cleaned numeric values (no unit suffixes).
    """
    pool = tickers or _TICKERS_SMALL
    return pd.DataFrame(
        {
            "Ticker": [pool[i % len(pool)] for i in range(n_rows)],
            "Net Dividend": [50.0 + (i % 100) for i in range(n_rows)],
            "Tax Collected": [15.0 + (i % 5) for i in range(n_rows)],
            "Shares": [100 + i for i in range(n_rows)],
        }
    )


def _build_tsv_file(tmp_path: Path, n_rows: int) -> Path:
    """Serialise a synthetic portfolio to a TSV file with realistic suffixes.

    Args:
        tmp_path: Directory where the file will be written.
        n_rows: Number of data rows (excluding header).

    Returns:
        Absolute ``Path`` pointing to the created ``.csv`` file.
    """
    df = _build_portfolio_df(n_rows)
    df["Net Dividend"] = df["Net Dividend"].astype(str) + " USD"
    df["Tax Collected"] = df["Tax Collected"].astype(str) + "%"
    file_path = tmp_path / f"portfolio_{n_rows}.csv"
    df.to_csv(file_path, sep="\t", index=False)
    return file_path


# ===========================================================================
# BENCHMARK GROUP 1 – DividendCalculator pure calculations
# ===========================================================================


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
    def test_projections_various_growth_rates(
        self, benchmark: pytest.fixture, growth_rate: float
    ) -> None:
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
    def test_growth_info_scaling_with_years(
        self, benchmark: pytest.fixture, years: int
    ) -> None:
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
    def test_currency_symbol_lookup(
        self, benchmark: pytest.fixture, ticker: str
    ) -> None:
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
        DividendCalculator.calculate_projections(
            _INITIAL_DIVIDEND, _GROWTH_RATE, _YEARS_LONG
        )
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_kib = peak_bytes / 1024
        assert peak_kib < 256, (
            f"Projection allocated {peak_kib:.1f} KiB – expected < 256 KiB"
        )


# ===========================================================================
# BENCHMARK GROUP 2 – DividendDataProcessor I/O
# ===========================================================================


@pytest.mark.benchmark
class TestDataProcessorPerformance:
    """Benchmarks for CSV loading and DataFrame filtering in DividendDataProcessor.

    Fixtures use ``tmp_path`` so every test gets a real, but temporary, file.
    """

    # -----------------------------------------------------------------------
    # Load from disk
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        "n_rows", _SCALE_ROWS, ids=[f"{n}rows" for n in _SCALE_ROWS]
    )
    def test_load_and_clean_data(
        self, benchmark: pytest.fixture, tmp_path: Path, n_rows: int
    ) -> None:
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

    def test_filter_single_ticker(
        self, benchmark: pytest.fixture, tmp_path: Path
    ) -> None:
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

    def test_filter_all_tickers(
        self, benchmark: pytest.fixture, tmp_path: Path
    ) -> None:
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

    def test_filter_empty_selection(
        self, benchmark: pytest.fixture, tmp_path: Path
    ) -> None:
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

    def test_full_pipeline_500_rows(
        self, benchmark: pytest.fixture, tmp_path: Path
    ) -> None:
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
        assert peak_mib < 4, (
            f"Loading 1 000 rows allocated {peak_mib:.2f} MiB – expected < 4 MiB"
        )


# ===========================================================================
# BENCHMARK GROUP 3 – ColorManager
# ===========================================================================


@pytest.mark.benchmark
class TestColorManagerPerformance:
    """Benchmarks for ColorManager colour assignment and HTML tile generation."""

    # -----------------------------------------------------------------------
    # generate_colors_for_tickers
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        "tickers",
        [_TICKERS_SMALL, _TICKERS_MEDIUM, _TICKERS_LARGE],
        ids=["4-tickers", "50-tickers", "200-tickers"],
    )
    def test_generate_colors_for_tickers(
        self, benchmark: pytest.fixture, tickers: list[str]
    ) -> None:
        """Benchmark: colour assignment scales linearly with ticker count.

        Args:
            benchmark: pytest-benchmark fixture.
            tickers: Pool of ticker symbols to assign colours to.
        """
        manager = ColorManager()
        result = benchmark(manager.generate_colors_for_tickers, tickers)

        assert len(result) == len(set(tickers))
        if len(tickers) <= 100:
            assert benchmark.stats["mean"] < _MAX_COLOR_GEN_100_SEC

    def test_repeated_color_generation_consistency(
        self, benchmark: pytest.fixture
    ) -> None:
        """Benchmark: repeated calls with the same tickers are idempotent and fast.

        The colour map for a sorted ticker list must be deterministic across
        multiple calls – no randomness, no state leakage.

        Args:
            benchmark: pytest-benchmark fixture.
        """
        manager = ColorManager()

        # Seed the manager before benchmarking so every round starts fresh.
        def _regenerate() -> dict[str, str]:
            return manager.generate_colors_for_tickers(_TICKERS_SMALL)

        first = manager.generate_colors_for_tickers(_TICKERS_SMALL)
        result = benchmark(_regenerate)

        assert result == first

    # -----------------------------------------------------------------------
    # create_tile_html
    # -----------------------------------------------------------------------

    def test_create_tile_html_single(self, benchmark: pytest.fixture) -> None:
        """Benchmark: HTML tile generation for one ticker.

        A new ``ColorManager`` is created inside the benchmark callable so
        the colour pool is never depleted across repeated measurement rounds.

        Args:
            benchmark: pytest-benchmark fixture.
        """

        def _make_tile() -> str:
            return ColorManager().create_tile_html("AAPL.US", 250)

        result = benchmark(_make_tile)
        assert "AAPL.US" in result
        assert "250" in result

    @pytest.mark.parametrize(
        "n_tiles", [4, 7, 9], ids=["4-tiles", "7-tiles", "9-tiles"]
    )
    def test_create_tile_html_batch(
        self, benchmark: pytest.fixture, n_tiles: int
    ) -> None:
        """Benchmark: generating HTML for a batch of tiles within colour-pool capacity.

        ``BASE_COLORS`` contains 10 unique colours.  Each test is capped at
        9 tiles so the available-colour pool is never exhausted within a
        single ``ColorManager`` instance.  A fresh instance is created per
        benchmark round to avoid cross-round state accumulation.

        Args:
            benchmark: pytest-benchmark fixture.
            n_tiles: Number of tile HTML fragments to generate per call.
        """
        tickers = [f"TICK{i:03d}.US" for i in range(n_tiles)]

        def _generate_all() -> list[str]:
            mgr = ColorManager()
            return [mgr.create_tile_html(t, 100 + i) for i, t in enumerate(tickers)]

        tiles = benchmark(_generate_all)
        assert len(tiles) == n_tiles
        assert all(isinstance(h, str) and len(h) > 0 for h in tiles)

    # -----------------------------------------------------------------------
    # get_random_base_color  (colour cycling)
    # -----------------------------------------------------------------------

    def test_get_random_base_color_100_draws(self, benchmark: pytest.fixture) -> None:
        """Benchmark: 100 colour draws using fresh manager instances.

        ``BASE_COLORS`` has 10 unique entries.  Drawing more than 9 colours
        from a single ``ColorManager`` exhausts the pool before the internal
        reset triggers (reset fires at ``len(used_colors) >= 20``, but all 10
        unique colours are gone after 10 draws).  Each draw therefore uses a
        fresh instance to measure pure per-call overhead without hitting the
        pool-exhaustion edge case.

        Args:
            benchmark: pytest-benchmark fixture.
        """

        def _draw_100() -> list[str]:
            return [ColorManager().get_random_base_color() for _ in range(100)]

        colors = benchmark(_draw_100)
        assert len(colors) == 100
        assert all(isinstance(c, str) for c in colors)

    # -----------------------------------------------------------------------
    # Memory – tracemalloc
    # -----------------------------------------------------------------------

    def test_tile_html_memory_50_tiles(self) -> None:
        """Verify 50 tile HTML fragments allocate < 1 MiB.

        HTML strings for 50 tiles should collectively stay well under a
        single megabyte of additional heap usage.  A fresh ``ColorManager``
        instance is created for each tile so that ``get_random_base_color``
        never exhausts the available colour pool within a single object
        (``BASE_COLORS`` contains 10 unique colours – reusing the same
        instance across more than 10 tiles would deplete the pool).
        """
        tickers = [f"TICK{i:03d}.US" for i in range(50)]

        tracemalloc.start()
        tiles = [ColorManager().create_tile_html(t, 100) for t in tickers]
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        _ = tiles  # Prevent optimisation
        peak_kib = peak_bytes / 1024
        assert peak_kib < 1024, (
            f"50 tiles used {peak_kib:.1f} KiB – expected < 1 024 KiB"
        )


# ===========================================================================
# BENCHMARK GROUP 4 – colour utility functions
# ===========================================================================


@pytest.mark.benchmark
class TestColorUtilsPerformance:
    """Benchmarks for module-level colour helper functions in color_manager.

    These helpers are called on every render cycle for each ticker, so
    even small per-call overhead is multiplied by portfolio size.
    """

    # -----------------------------------------------------------------------
    # hex_to_rgba
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize("hex_color", _SAMPLE_HEX_COLORS)
    def test_hex_to_rgba_conversion(
        self, benchmark: pytest.fixture, hex_color: str
    ) -> None:
        """Benchmark: hex → rgba conversion for all sample colours.

        Args:
            benchmark: pytest-benchmark fixture.
            hex_color: Input hex colour string.
        """
        result = benchmark(hex_to_rgba, hex_color, 0.8)
        assert result.startswith("rgba(")

    def test_hex_to_rgba_batch_200(self, benchmark: pytest.fixture) -> None:
        """Benchmark: converting 200 hex colours in one call batch.

        Args:
            benchmark: pytest-benchmark fixture.
        """

        def _batch() -> list[str]:
            return [
                hex_to_rgba(_SAMPLE_HEX_COLORS[i % len(_SAMPLE_HEX_COLORS)], 0.5)
                for i in range(200)
            ]

        results = benchmark(_batch)
        assert len(results) == 200

    # -----------------------------------------------------------------------
    # rgb_to_hex
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize("rgb_color", _SAMPLE_RGB_COLORS)
    def test_rgb_to_hex_conversion(
        self, benchmark: pytest.fixture, rgb_color: str
    ) -> None:
        """Benchmark: rgb → hex conversion for all sample colours.

        Args:
            benchmark: pytest-benchmark fixture.
            rgb_color: Input rgb() formatted colour string.
        """
        result = benchmark(rgb_to_hex, rgb_color)
        assert result.startswith("#")
        assert len(result) == 7

    # -----------------------------------------------------------------------
    # adjust_gradient
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        "color",
        ["#FF6B6B", "#000000", "#FFFFFF", "rgb(78, 205, 196)"],
        ids=["pastel-red", "black", "white", "rgb-string"],
    )
    def test_adjust_gradient(self, benchmark: pytest.fixture, color: str) -> None:
        """Benchmark: gradient lightening for various input formats.

        Args:
            benchmark: pytest-benchmark fixture.
            color: Input colour in hex or rgb format.
        """
        result = benchmark(adjust_gradient, color)
        assert result.startswith("rgb(")

    # -----------------------------------------------------------------------
    # apply_wcag_ui_standards
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        "color,expected_light",
        [
            ("#FFFFFF", True),
            ("#000000", False),
            ("#8A2BE2", False),
            ("#FFFF00", True),
        ],
        ids=["white", "black", "purple", "yellow"],
    )
    def test_wcag_luminance(
        self,
        benchmark: pytest.fixture,
        color: str,
        expected_light: bool,
    ) -> None:
        """Benchmark: WCAG luminance calculation is fast and correct.

        Args:
            benchmark: pytest-benchmark fixture.
            color: Input hex colour.
            expected_light: Expected return value of ``apply_wcag_ui_standards``.
        """
        result = benchmark(apply_wcag_ui_standards, color)
        assert result == expected_light

    # -----------------------------------------------------------------------
    # determine_text_color_for_dropdown
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        "bg_color,expected_text",
        [
            ("#FFFFFF", "#000000"),
            ("#000000", "#FFFFFF"),
            ("#8A2BE2", "#FFFFFF"),
        ],
        ids=["light-bg", "dark-bg", "purple-bg"],
    )
    def test_determine_text_color(
        self,
        benchmark: pytest.fixture,
        bg_color: str,
        expected_text: str,
    ) -> None:
        """Benchmark: text colour selection returns a valid CSS colour string.

        Args:
            benchmark: pytest-benchmark fixture.
            bg_color: Background hex colour.
            expected_text: Expected ``"#000000"`` or ``"#FFFFFF"`` text colour.
        """
        result = benchmark(determine_text_color_for_dropdown, bg_color)
        assert result == expected_text


# ===========================================================================
# BENCHMARK GROUP 5 – scale / stress tests
# ===========================================================================


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
            return [
                DividendCalculator.calculate_projections(d, _GROWTH_RATE, _YEARS_MEDIUM)
                for d in dividends
            ]

        results = benchmark.pedantic(_project_all, rounds=5, warmup_rounds=2)
        assert len(results) == 100
        assert all(len(df) == _YEARS_MEDIUM for df in results)

    def test_full_render_cycle_1000_rows(
        self, benchmark: pytest.fixture, tmp_path: Path
    ) -> None:
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
                    projections[ticker] = DividendCalculator.calculate_projections(
                        initial, _GROWTH_RATE, _YEARS_SHORT
                    )

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
            return [
                ColorManager().create_tile_html(ticker, 100 + i)
                for i, ticker in enumerate(_TICKERS_LARGE)
            ]

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
                DividendCalculator.calculate_projections(
                    initial, _GROWTH_RATE, _YEARS_SHORT
                )

        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mib = peak_bytes / (1024**2)
        assert peak_mib < 16, f"Full cycle used {peak_mib:.2f} MiB – expected < 16 MiB"
