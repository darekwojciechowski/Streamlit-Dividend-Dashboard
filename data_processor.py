"""
Data Processor for Dividend Data

This module defines the DividendDataProcessor class, responsible for loading,
cleaning, and filtering dividend data from a specified CSV file.

The class expects a tab-separated CSV file with specific columns related to
dividend information (Ticker, Net Dividend, Tax Collected, Shares).

Methods:
- load_data: Loads the data from the CSV file using pandas.
- clean_data: Cleans column names and converts data types for relevant columns
              (Net Dividend, Tax Collected, Shares).
- filter_data: Filters the DataFrame based on a list of selected stock tickers.
"""

import pandas as pd
# Removed unused imports: random, numpy

class DividendDataProcessor:
    """Handles loading, cleaning, and filtering of dividend data."""

    def __init__(self, file_path: str):
        """
        Initializes the processor, loads and cleans the data.

        Args:
            file_path (str): The path to the tab-separated CSV file.
        """
        self.file_path = file_path
        try:
            self.df = self.load_data()
            self.clean_data()
            # Add a check for essential columns after loading and cleaning
            required_cols = ['Ticker', 'Net Dividend', 'Tax Collected', 'Shares']
            if not all(col in self.df.columns for col in required_cols):
                missing = [col for col in required_cols if col not in self.df.columns]
                raise ValueError(f"CSV file is missing required columns: {', '.join(missing)}")
        except FileNotFoundError:
            print(f"Error: The file was not found at {self.file_path}")
            # Optionally, raise the error or handle it by setting df to None or empty
            raise # Re-raise the exception to stop execution if file is critical
        except Exception as e:
            print(f"An error occurred during data processing initialization: {e}")
            raise # Re-raise for clarity

    def load_data(self) -> pd.DataFrame:
        """
        Loads data from the CSV file specified by self.file_path.

        Assumes the separator is a tab ('\t').

        Returns:
            pd.DataFrame: The loaded data as a pandas DataFrame.

        Raises:
            FileNotFoundError: If the file specified by self.file_path does not exist.
            pd.errors.EmptyDataError: If the file is empty.
            Exception: For other potential pandas read_csv errors.
        """
        print(f"Loading data from: {self.file_path}") # Added print for debugging
        return pd.read_csv(self.file_path, sep="\t")

    def clean_data(self):
        """
        Cleans and processes the DataFrame stored in self.df.

        - Strips whitespace from column names.
        - Converts 'Net Dividend' to float after removing ' USD'.
        - Converts 'Tax Collected' to float after removing '%'.
        - Converts 'Shares' to float.

        Handles potential errors during conversion.
        """
        if self.df is None or self.df.empty:
            print("Warning: DataFrame is empty or None. Skipping cleaning.")
            return

        self.df.columns = self.df.columns.str.strip()

        # Define columns to clean and their cleaning logic
        cleaning_map = {
            'Net Dividend': lambda x: x.str.replace(' USD', '', regex=False),
            'Tax Collected': lambda x: x.str.replace('%', '', regex=False),
            'Shares': None # No string replacement needed, just type conversion
        }

        for col, clean_func in cleaning_map.items():
            if col in self.df.columns:
                try:
                    # Apply string cleaning if a function is provided
                    if clean_func:
                        self.df[col] = clean_func(self.df[col])
                    # Convert to float, coercing errors to NaN
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                except Exception as e:
                    print(f"Warning: Could not clean or convert column '{col}'. Error: {e}")
            else:
                print(f"Warning: Expected column '{col}' not found for cleaning.")

        # Optionally, handle NaNs created by 'coerce'
        # Example: self.df.dropna(subset=['Net Dividend', 'Shares'], inplace=True)

    def filter_data(self, selected_tickers: list) -> pd.DataFrame:
        """
        Filters the DataFrame based on a list of selected tickers.

        Args:
            selected_tickers (list): A list of ticker symbols (strings) to filter by.

        Returns:
            pd.DataFrame: A new DataFrame containing only the rows for the selected tickers.
                          Returns an empty DataFrame if the input list is empty or
                          if the original DataFrame is empty/None.
        """
        if self.df is None or self.df.empty:
            return pd.DataFrame() # Return empty DataFrame if no data
        if not selected_tickers:
            return pd.DataFrame() # Return empty DataFrame if no tickers selected

        # Ensure 'Ticker' column exists
        if 'Ticker' not in self.df.columns:
             print("Warning: 'Ticker' column not found for filtering.")
             return pd.DataFrame()

        return self.df[self.df['Ticker'].isin(selected_tickers)].copy() # Return a copy to avoid SettingWithCopyWarning