"""Performance benchmarks for ColorManager colour assignment and HTML tile generation."""

from __future__ import annotations

import tracemalloc

import pytest
from app.utils.color_manager import ColorManager

from .conftest import (
    _MAX_COLOR_GEN_100_SEC,
    _TICKERS_LARGE,
    _TICKERS_MEDIUM,
    _TICKERS_SMALL,
)


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
    def test_generate_colors_for_tickers(self, benchmark: pytest.fixture, tickers: list[str]) -> None:
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

    def test_repeated_color_generation_consistency(self, benchmark: pytest.fixture) -> None:
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

    @pytest.mark.parametrize("n_tiles", [4, 7, 9], ids=["4-tiles", "7-tiles", "9-tiles"])
    def test_create_tile_html_batch(self, benchmark: pytest.fixture, n_tiles: int) -> None:
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
        assert peak_kib < 1024, f"50 tiles used {peak_kib:.1f} KiB – expected < 1 024 KiB"
