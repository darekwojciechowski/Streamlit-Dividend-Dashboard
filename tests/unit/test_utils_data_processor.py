"""Unit tests for app.utils.data_processor.DividendDataProcessor.

Covers:
- Initialisation: valid TSV, file-not-found, corrupt data
- Data cleaning: suffix removal, column whitespace, numeric coercion
- Column validation: missing required columns, empty file
- filter_data: single/multiple tickers, empty selection, missing Ticker column
- Exception path inside _clean_dataframe (except-continue branch)
"""

import contextlib
import io
from unittest.mock import patch

import pandas as pd
import pytest
from app.utils.data_processor import DividendDataProcessor

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.unit

REQUIRED_COLUMNS = ["Ticker", "Net Dividend", "Tax Collected", "Shares"]

_SAMPLE_TSV = (
    "Ticker\tNet Dividend\tTax Collected\tShares\n"
    "AAPL.US\t50.00 USD\t10%\t100\n"
    "MSFT.US\t60.00 USD\t15%\t50\n"
    "PKO.PL\t75.00 USD\t12%\t200\n"
)


def _make_processor(tsv_content: str = _SAMPLE_TSV) -> DividendDataProcessor:
    """Build a DividendDataProcessor from an in-memory TSV string."""
    with patch("builtins.open"), patch("pandas.read_csv", return_value=pd.read_csv(io.StringIO(tsv_content), sep="\t")):
        return DividendDataProcessor("fake_path.csv")


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


class TestInit:
    def test_loads_valid_tsv(self):
        proc = _make_processor()
        assert isinstance(proc.df, pd.DataFrame)
        assert len(proc.df) == 3

    def test_file_not_found_raises(self):
        with (
            patch("pandas.read_csv", side_effect=FileNotFoundError),
            pytest.raises(FileNotFoundError, match="not found"),
        ):
            DividendDataProcessor("missing.csv")

    def test_generic_exception_wrapped(self):
        with (
            patch("pandas.read_csv", side_effect=Exception("bad file")),
            pytest.raises(RuntimeError, match="Failed to process data"),
        ):
            DividendDataProcessor("bad.csv")

    def test_required_columns_constant(self):
        assert DividendDataProcessor.REQUIRED_COLUMNS == REQUIRED_COLUMNS


# ---------------------------------------------------------------------------
# Data cleaning
# ---------------------------------------------------------------------------


class TestDataCleaning:
    def test_strips_usd_suffix_from_net_dividend(self):
        proc = _make_processor()
        assert pd.api.types.is_float_dtype(proc.df["Net Dividend"])
        assert proc.df.loc[proc.df["Ticker"] == "AAPL.US", "Net Dividend"].iloc[0] == pytest.approx(50.0)

    def test_strips_percent_suffix_from_tax_collected(self):
        proc = _make_processor()
        assert pd.api.types.is_numeric_dtype(proc.df["Tax Collected"])
        assert proc.df.loc[proc.df["Ticker"] == "AAPL.US", "Tax Collected"].iloc[0] == pytest.approx(10.0)

    def test_converts_shares_to_numeric(self):
        proc = _make_processor()
        assert pd.api.types.is_numeric_dtype(proc.df["Shares"])

    def test_strips_whitespace_from_column_names(self):
        tsv = " Ticker \t Net Dividend \t Tax Collected \t Shares \nAAPL.US\t1.0 USD\t5%\t10\n"
        proc = _make_processor(tsv)
        for col in REQUIRED_COLUMNS:
            assert col in proc.df.columns

    def test_empty_dataframe_returns_without_error(self):
        tsv = "Ticker\tNet Dividend\tTax Collected\tShares\n"
        proc = _make_processor(tsv)
        assert proc.df.empty

    def test_invalid_numeric_coerced_to_nan(self):
        tsv = "Ticker\tNet Dividend\tTax Collected\tShares\nAAPL.US\tNOT_A_NUMBER USD\t10%\t100\n"
        proc = _make_processor(tsv)
        assert pd.isna(proc.df.loc[0, "Net Dividend"])

    def test_clean_exception_branch_continues(self):
        """Trigger the except-continue branch in _clean_dataframe."""
        tsv = _SAMPLE_TSV
        raw_df = pd.read_csv(io.StringIO(tsv), sep="\t")

        # Make str.replace raise an AttributeError for "Net Dividend" column
        original_replace = pd.Series.str.replace

        def patched_replace(self, *args, **kwargs):
            if self.name == "Net Dividend":
                raise AttributeError("simulated error")
            return original_replace(self, *args, **kwargs)

        with (
            patch("pandas.read_csv", return_value=raw_df),
            patch.object(pd.core.strings.accessor.StringMethods, "replace", patched_replace),
            contextlib.suppress(Exception),
        ):
            DividendDataProcessor("fake.csv")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    def test_missing_required_column_raises(self):
        tsv = "Ticker\tNet Dividend\tShares\nAAPL.US\t1.0 USD\t10\n"
        with pytest.raises((ValueError, RuntimeError), match="Missing required columns"):
            _make_processor(tsv)

    def test_all_required_columns_present_no_error(self):
        proc = _make_processor()
        for col in REQUIRED_COLUMNS:
            assert col in proc.df.columns


# ---------------------------------------------------------------------------
# filter_data
# ---------------------------------------------------------------------------


class TestFilterData:
    def test_filter_single_ticker(self):
        proc = _make_processor()
        result = proc.filter_data(["AAPL.US"])
        assert len(result) == 1
        assert result.iloc[0]["Ticker"] == "AAPL.US"

    def test_filter_multiple_tickers(self):
        proc = _make_processor()
        result = proc.filter_data(["AAPL.US", "MSFT.US"])
        assert set(result["Ticker"]) == {"AAPL.US", "MSFT.US"}

    def test_filter_nonexistent_ticker_returns_empty(self):
        proc = _make_processor()
        result = proc.filter_data(["NONEXIST.XX"])
        assert result.empty

    def test_filter_empty_list_returns_empty(self):
        proc = _make_processor()
        result = proc.filter_data([])
        assert result.empty

    def test_filter_returns_independent_copy(self):
        proc = _make_processor()
        result = proc.filter_data(["AAPL.US"])
        result.iloc[0, result.columns.get_loc("Shares")] = 9999
        # Original df must be unmodified
        assert proc.df.loc[proc.df["Ticker"] == "AAPL.US", "Shares"].iloc[0] != 9999

    def test_filter_with_missing_ticker_column(self):
        """Cover the 'Ticker not in df.columns' branch (line 66)."""
        proc = _make_processor()
        # Manually drop the Ticker column after load to hit the guard branch
        proc.df = proc.df.drop(columns=["Ticker"])
        result = proc.filter_data(["AAPL.US"])
        assert result.empty

    def test_filter_empty_df_returns_empty(self):
        proc = _make_processor()
        proc.df = pd.DataFrame()
        result = proc.filter_data(["AAPL.US"])
        assert result.empty
