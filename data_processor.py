"""Data processor for loading, cleaning, and filtering dividend data."""

import pandas as pd


class DividendDataProcessor:
    """Handles loading, cleaning, and filtering of dividend data."""

    REQUIRED_COLUMNS = ['Ticker', 'Net Dividend', 'Tax Collected', 'Shares']

    def __init__(self, file_path: str):
        """Initialize processor and load data."""
        self.file_path = file_path
        self.df = self._load_and_clean_data()

    def _load_and_clean_data(self) -> pd.DataFrame:
        """Load and clean data from CSV file."""
        try:
            df = pd.read_csv(self.file_path, sep="\t")
            self._clean_dataframe(df)
            self._validate_columns(df)
            return df
        except FileNotFoundError:
            raise FileNotFoundError(f"Data file not found at {self.file_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to process data: {e}")

    def _clean_dataframe(self, df: pd.DataFrame) -> None:
        """Clean the dataframe in-place."""
        if df.empty:
            return

        # Clean column names
        df.columns = df.columns.str.strip()

        # Clean and convert specific columns
        cleaning_rules = {
            'Net Dividend': lambda x: x.str.replace(' USD', '', regex=False),
            'Tax Collected': lambda x: x.str.replace('%', '', regex=False),
            'Shares': None  # Just convert to numeric
        }

        for column, cleaner in cleaning_rules.items():
            if column in df.columns:
                try:
                    if cleaner:
                        df[column] = cleaner(df[column])
                    df[column] = pd.to_numeric(df[column], errors='coerce')
                except Exception:
                    continue  # Skip problematic columns

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Validate that required columns exist."""
        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

    def filter_data(self, selected_tickers: list) -> pd.DataFrame:
        """Filter data by selected tickers."""
        if self.df is None or self.df.empty or not selected_tickers:
            return pd.DataFrame()

        if 'Ticker' not in self.df.columns:
            return pd.DataFrame()

        return self.df[self.df['Ticker'].isin(selected_tickers)].copy()
