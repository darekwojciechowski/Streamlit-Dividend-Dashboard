"""Dividend calculator utilities."""

import pandas as pd
from typing import Optional


class DividendCalculator:
    """Handles dividend calculations and projections."""

    @staticmethod
    def get_currency_symbol(ticker: str) -> str:
        """Get currency symbol based on ticker country code."""
        if "." in ticker:
            country_code = ticker.split(".")[-1]
            currency_map = {
                "PL": "PLN",
                "US": "$",
                "EU": "€"
            }
            return currency_map.get(country_code, "$")
        return "$"

    @staticmethod
    def get_initial_dividend(ticker_data: pd.DataFrame) -> Optional[float]:
        """Extract initial dividend from ticker data."""
        if ticker_data.empty or "Net Dividend" not in ticker_data.columns:
            return None

        dividend_series = ticker_data["Net Dividend"].dropna()
        if dividend_series.empty:
            return None

        initial_dividend = dividend_series.iloc[0]
        return initial_dividend if initial_dividend > 0 else None

    @staticmethod
    def calculate_projections(initial_dividend: float, growth_rate: float, years: int) -> pd.DataFrame:
        """Calculate dividend projections over specified years."""
        current_year = pd.Timestamp.now().year
        year_range = list(range(current_year, current_year + years))

        projected_dividends = [
            initial_dividend * (1 + growth_rate / 100) ** i
            for i in range(years)
        ]

        return pd.DataFrame({
            "Year": year_range,
            "Projected Dividend": projected_dividends
        })
