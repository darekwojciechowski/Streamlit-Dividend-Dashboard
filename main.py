"""
Streamlit Dividend Dashboard Application

This is the main script for the Streamlit Dividend Dashboard application.
It orchestrates the user interface, data processing, and visualization
for analyzing stock dividend data.

The application allows users to:
- Load and view dividend data for selected stock tickers.
- See key metrics like total shares held per ticker displayed in interactive tiles.
- Visualize dividend amounts and distribution using Plotly bar and pie charts.
- Project future dividend growth based on user-defined growth rates and time periods.

It utilizes helper modules for data processing (`data_processor.py`) and
styling (`styles/colors_and_styles.py`).

Author: [Your Name/GitHub Username]
Date: [Current Date, e.g., July 2024]
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import random
from data_processor import DividendDataProcessor
# Import necessary functions from the styles module
from styles.colors_and_styles import BASE_COLORS, CSS_STYLES, adjust_gradient, determine_text_color_for_dropdown

class DividendApp:
    """
    Main class for the Streamlit Dividend Dashboard application.
    Handles UI setup, data processing delegation, and display logic.
    """
    def __init__(self):
        """
        Initializes the application, sets page configuration,
        and loads initial data using DividendDataProcessor.
        """
        # Set page config - should be the first Streamlit command
        st.set_page_config(
            page_title="Dividend Dashboard",
            initial_sidebar_state="expanded"
        )
        try:
            self.data_processor = DividendDataProcessor("data/dividend_data.csv")
        except Exception as e:
            st.error(f"Failed to initialize data processor: {e}")
            st.stop() # Stop execution if data cannot be loaded/processed

        self.filtered_df = pd.DataFrame() # Initialize as empty DataFrame
        self.aggregated_shares = pd.DataFrame(columns=['Ticker', 'Shares']) # Initialize empty
        self.ticker_colors = {}
        self.selected_tickers = []
        self.selected_ticker = None
        self.growth_percentage = 4.0 # Default growth percentage
        self.num_years = 15 # Default number of years
        self.base_colors = BASE_COLORS

    def run(self):
        """
        Executes the main application flow:
        UI setup -> Data Filtering -> Aggregation -> Display Metrics/Charts/Calculator.
        """
        self.setup_ui()
        self.filter_data()
        self.aggregate_shares()
        self.display_metrics()
        self.display_charts() # This generates self.ticker_colors
        self.display_dividend_calculator() # This uses self.ticker_colors

    def setup_ui(self):
        """Sets up the main UI elements like title and ticker selection."""
        st.title('Dividend Data Visualization Dashboard')
        # Ensure data_processor.df is valid before accessing unique()
        if self.data_processor.df is not None and not self.data_processor.df.empty:
            all_tickers = sorted(self.data_processor.df['Ticker'].unique()) # Sort tickers alphabetically
            self.selected_tickers = st.multiselect(
                'Select tickers to analyze:',
                options=all_tickers,
                default=list(all_tickers) # Default to all tickers selected
            )
        else:
            st.warning("No ticker data available to select.")
            self.selected_tickers = []


    def filter_data(self):
        """Filters the main DataFrame based on user-selected tickers."""
        if not self.selected_tickers:
            # If no tickers selected, keep filtered_df empty or show a message
            self.filtered_df = pd.DataFrame()
            # Optionally: st.info("Select tickers to see data.")
        elif self.data_processor.df is not None:
            self.filtered_df = self.data_processor.filter_data(self.selected_tickers)
        else:
            self.filtered_df = pd.DataFrame()


    def aggregate_shares(self):
        """Aggregates total shares per ticker from the filtered data."""
        if not self.filtered_df.empty and 'Ticker' in self.filtered_df.columns and 'Shares' in self.filtered_df.columns:
            # Ensure Shares column is numeric before summing
            self.filtered_df['Shares'] = pd.to_numeric(self.filtered_df['Shares'], errors='coerce')
            self.aggregated_shares = self.filtered_df.groupby('Ticker', as_index=False).agg({'Shares': 'sum'})
        else:
            # Ensure aggregated_shares is an empty DataFrame with correct columns if no data
            self.aggregated_shares = pd.DataFrame(columns=['Ticker', 'Shares'])

    def _generate_tile(self, ticker: str, shares: float, color: str) -> str:
        """
        Generates the HTML for a single interactive tile displaying ticker shares.

        Args:
            ticker (str): The stock ticker symbol.
            shares (float): The aggregated number of shares for the ticker.
            color (str): The base background color for the tile (hex format).

        Returns:
            str: HTML string representing the tile.
        """
        gradient_color = adjust_gradient(color)
        text_color = determine_text_color_for_dropdown(color) # Use WCAG function

        # Format shares with commas, handle potential NaN/None
        formatted_shares = f"{shares:,.0f}" if pd.notna(shares) else "N/A"

        return f"""
        <div class="gradient-tile" style="
            background: linear-gradient(145deg, {color} 0%, {gradient_color} 100%);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem;
            color: {text_color}; /* Dynamically set text color */
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            min-width: 250px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        ">
            <div style="
                position: absolute;
                top: -20px;
                right: -20px;
                width: 60px;
                height: 60px;
                background: {gradient_color}40; /* Use alpha for subtle effect */
                border-radius: 50%;
            "></div>

            <h3 style="margin:0; font-size:1.5rem; position: relative; font-weight:600;">{ticker}</h3>
            <p style="font-size:2.5rem; margin:0.5rem 0; font-weight:800; position: relative;">
                {formatted_shares}<span style="font-size:1rem; font-weight:500;"> shares</span>
            </p>
        </div>
        """


    def display_metrics(self):
        """Displays the key metrics (total shares) using generated tiles."""
        st.markdown("## Total Shares per Ticker")
        st.markdown(CSS_STYLES, unsafe_allow_html=True)

        if not self.aggregated_shares.empty:
            # Ensure base_colors is not empty
            if not self.base_colors:
                self.base_colors = ['#636EFA'] # Provide a default color if empty

            tiles_html = "".join(
                self._generate_tile(row['Ticker'], row['Shares'], random.choice(self.base_colors))
                for _, row in self.aggregated_shares.iterrows()
            )

            st.html(f"""
            <div class="tiles-container">
                {tiles_html}
            </div>
            """)
        else:
            st.info("No share data to display metrics for the selected tickers.")


    def display_charts(self):
        """Displays the Plotly bar and pie charts for dividend analysis."""
        st.markdown("## Dividend Analysis Charts")
        if not self.filtered_df.empty:
            # Define ticker colors using a qualitative palette
            unique_tickers = sorted(self.filtered_df['Ticker'].unique()) # Sort for consistent color assignment
            if len(unique_tickers) > 0:
                 # Use a palette suitable for the number of unique tickers
                 # Cycle through colors if more tickers than colors in palette
                 color_palette = px.colors.qualitative.Pastel
                 self.ticker_colors = {ticker: color_palette[i % len(color_palette)] for i, ticker in enumerate(unique_tickers)}
            else:
                 self.ticker_colors = {}


            # Check if 'Net Dividend' data is available and valid
            if 'Net Dividend' in self.filtered_df.columns and self.filtered_df['Net Dividend'].notna().any():
                # Aggregate data for charts to avoid plotting individual transactions if multiple per ticker
                chart_data = self.filtered_df.groupby('Ticker', as_index=False)['Net Dividend'].sum()
                # Ensure chart_data is sorted consistent with unique_tickers if needed, though color_discrete_map handles mapping
                chart_data = chart_data.sort_values('Ticker').reset_index(drop=True)


                fig_bar = px.bar(chart_data, x='Ticker', y='Net Dividend', color='Ticker',
                                 title="Total Net Dividends by Ticker",
                                 color_discrete_map=self.ticker_colors)
                fig_bar.update_layout(xaxis_title="Ticker", yaxis_title="Total Net Dividend (USD)", hovermode='x unified')
                st.plotly_chart(fig_bar, use_container_width=True)

                fig_donut = px.pie(chart_data, names='Ticker', values='Net Dividend',
                                   title="Share of Total Net Dividends by Ticker", color='Ticker',
                                   color_discrete_map=self.ticker_colors, hole=0.4)
                # Ensure pull length matches number of unique tickers in chart_data
                pull_values = [0.05] * len(chart_data['Ticker'].unique())
                fig_donut.update_traces(textinfo='percent+label', pull=pull_values)
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("No valid 'Net Dividend' data available for the selected tickers to display charts.")
        else:
            st.info("No data to display charts for the selected tickers.")


    def display_dividend_calculator(self):
        """Displays the UI for the dividend growth calculator."""
        st.markdown("---")
        st.subheader("Dividend Growth Calculator")
        st.write("Project future dividend income based on selected annual growth rate and investment period.")
        st.write("")

        # Ensure filtered_df is not empty before showing calculator inputs
        if self.filtered_df.empty:
            st.warning("Please select tickers with data to use the calculator.")
            return

        col1, col2 = st.columns(2)
        with col1:
            available_tickers = sorted(self.filtered_df['Ticker'].unique()) # Sort tickers
            if not available_tickers: # Check if list is empty
                 st.warning("No tickers available for calculation.")
                 return
            # Use session state to remember the selected ticker if needed, otherwise default to first
            self.selected_ticker = st.selectbox("Select a company for projection:", available_tickers, index=0, key="calculator_ticker_select")
        with col2:
            self.growth_percentage = st.number_input("Annual dividend growth (%)", min_value=0.0, step=0.1, value=self.growth_percentage, format="%.1f", key="calculator_growth_input")

        self.num_years = st.slider("Projection years", min_value=1, max_value=30, value=self.num_years, key="calculator_years_slider")
        self._display_projection_chart()

    def _display_projection_chart(self):
        """Calculates and displays the projected dividend growth chart using the ticker's assigned color."""
        if not self.selected_ticker:
            st.info("Select a ticker to see the projection.")
            return

        ticker_data = self.filtered_df[self.filtered_df['Ticker'] == self.selected_ticker]

        if ticker_data.empty:
            st.warning(f"No data found for selected ticker: {self.selected_ticker}")
            return

        if 'Net Dividend' not in ticker_data.columns or ticker_data['Net Dividend'].isnull().all():
            st.warning(f"No 'Net Dividend' data available for {self.selected_ticker}.")
            return

        # Use the first available non-null dividend entry for the ticker as the base
        initial_dividend_series = ticker_data['Net Dividend'].dropna()
        if initial_dividend_series.empty:
             st.warning(f"No valid initial dividend found for {self.selected_ticker}.")
             return
        initial_dividend = initial_dividend_series.iloc[0]


        if initial_dividend <= 0:
             st.warning(f"Initial dividend for {self.selected_ticker} is zero or negative ({initial_dividend:.2f} USD). Cannot project growth.")
             return

        current_year = pd.Timestamp.now().year
        years = list(range(current_year, current_year + self.num_years))
        projected_dividends = [initial_dividend * (1 + self.growth_percentage / 100) ** i for i in range(self.num_years)]

        projected_df = pd.DataFrame({
            'Year': years,
            'Projected Dividend (USD)': projected_dividends,
            'Ticker': [self.selected_ticker] * self.num_years
        })

        # --- Get the color for the selected ticker from self.ticker_colors ---
        # Check if ticker_colors exists and has the selected ticker
        if hasattr(self, 'ticker_colors') and self.ticker_colors and self.selected_ticker in self.ticker_colors:
            chart_color = self.ticker_colors[self.selected_ticker]
        else:
            # Fallback color if ticker_colors isn't ready or ticker is missing
            chart_color = '#1f77b4' # Default Plotly blue or another sensible default
            # Optionally print a warning if this happens unexpectedly
            # print(f"Warning: Color for ticker {self.selected_ticker} not found in ticker_colors. Using default.")


        fig_projected = px.bar(projected_df, x='Year', y='Projected Dividend (USD)',
                               title=f"Projected Dividends for {self.selected_ticker} (Starting from {initial_dividend:.2f} USD)",
                               color_discrete_sequence=[chart_color]) # Apply the looked-up color
        fig_projected.update_layout(xaxis_title="Year", yaxis_title="Projected Dividend (USD)", hovermode='x unified')

        # Add scatter plot for the trend line using the same color
        fig_projected.add_scatter(x=projected_df['Year'], y=projected_dividends, mode='lines+markers',
                                 name='Projected Trend', line=dict(color='#EF553B', width=2, dash='dot'), marker=dict(size=5)) # Apply the looked-up color

        st.plotly_chart(fig_projected, use_container_width=True)


if __name__ == "__main__":
    # Instantiate and run the app
    app = DividendApp()
    app.run()