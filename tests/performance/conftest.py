"""Shared constants and helper functions for performance benchmarks."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

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
# Shared helpers
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
