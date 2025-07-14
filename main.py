from typing import Dict, List, Optional, Tuple
import streamlit as st
import pandas as pd
import plotly.express as px
import random
from data_processor import DividendDataProcessor
from components.nivo_pie_chart import NivoPieChart
from styles.colors_and_styles import (
    BASE_COLORS,
    CSS_STYLES,
    adjust_gradient,
    determine_text_color_for_dropdown,
)
from app_config import (
    DEFAULT_GROWTH_PERCENTAGE,
    DEFAULT_NUM_YEARS,
    DATA_FILE_PATH,
    COLOR_THEME,
    DEFAULT_PAGE_TITLE,
    DEFAULT_SIDEBAR_STATE,
    DEFAULT_LAYOUT,
)


class DividendApp:
    """
    Modern Streamlit Dividend Dashboard Application.

    Clean, maintainable implementation following Python 2025 best practices.
    Focused on separation of concerns and readability.
    """

    def __init__(self) -> None:
        """Initialize the application with default configuration."""
        self._configure_streamlit()
        self._initialize_data_processor()
        self._initialize_state()

    def _configure_streamlit(self) -> None:
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title=DEFAULT_PAGE_TITLE,
            initial_sidebar_state=DEFAULT_SIDEBAR_STATE,
            layout=DEFAULT_LAYOUT
        )

    def _initialize_data_processor(self) -> None:
        """Initialize the data processor with error handling."""
        try:
            self.data_processor = DividendDataProcessor(DATA_FILE_PATH)
        except Exception as e:
            st.error(f"Failed to initialize data processor: {e}")
            st.stop()

    def _initialize_state(self) -> None:
        """Initialize application state variables."""
        self.filtered_df = pd.DataFrame()
        self.aggregated_shares = pd.DataFrame(columns=["Ticker", "Shares"])
        self.ticker_colors: Dict[str, str] = {}
        self.selected_tickers: List[str] = []
        self.selected_ticker: Optional[str] = None

    def run(self) -> None:
        """Main application flow."""
        self._setup_ui()
        self._process_data()
        self._render_dashboard()

    def _setup_ui(self) -> None:
        """Setup the main user interface."""
        st.title("Dividend Analysis Dashboard")
        self._render_ticker_selector()

    def _render_ticker_selector(self) -> None:
        """Render the ticker selection widget."""
        if not self._has_valid_data():
            st.warning("No ticker data available to select.")
            return

        all_tickers = self._get_available_tickers()
        self.selected_tickers = st.multiselect(
            "Select tickers to analyze:",
            options=all_tickers,
            default=all_tickers,
            help="Choose one or more stock tickers for analysis"
        )

    def _has_valid_data(self) -> bool:
        """Check if data processor has valid data."""
        return (
            self.data_processor.df is not None
            and not self.data_processor.df.empty
        )

    def _get_available_tickers(self) -> List[str]:
        """Get sorted list of available tickers."""
        return sorted(self.data_processor.df["Ticker"].unique())

    def _process_data(self) -> None:
        """Process and filter data based on selections."""
        self._filter_data()
        self._aggregate_shares()
        self._generate_ticker_colors()

    def _filter_data(self) -> None:
        """Filter data based on selected tickers."""
        if not self.selected_tickers or not self._has_valid_data():
            self.filtered_df = pd.DataFrame()
            return

        self.filtered_df = self.data_processor.filter_data(
            self.selected_tickers)

    def _aggregate_shares(self) -> None:
        """Aggregate total shares per ticker."""
        if not self._has_shares_data():
            self.aggregated_shares = pd.DataFrame(columns=["Ticker", "Shares"])
            return

        self.filtered_df["Shares"] = pd.to_numeric(
            self.filtered_df["Shares"], errors="coerce"
        )
        self.aggregated_shares = self.filtered_df.groupby(
            "Ticker", as_index=False
        ).agg({"Shares": "sum"})

    def _has_shares_data(self) -> bool:
        """Check if filtered data has shares information."""
        return (
            not self.filtered_df.empty
            and "Ticker" in self.filtered_df.columns
            and "Shares" in self.filtered_df.columns
        )

    def _generate_ticker_colors(self) -> None:
        """Generate consistent colors for tickers."""
        if self.filtered_df.empty:
            self.ticker_colors = {}
            return

        unique_tickers = sorted(self.filtered_df["Ticker"].unique())
        color_palette = px.colors.qualitative.Pastel

        self.ticker_colors = {
            ticker: color_palette[i % len(color_palette)]
            for i, ticker in enumerate(unique_tickers)
        }

    def _render_dashboard(self) -> None:
        """Render the main dashboard components."""
        self._render_metrics_section()
        self._render_charts_section()
        self._render_calculator_section()

    def _render_metrics_section(self) -> None:
        """Render the metrics tiles section."""
        st.markdown("## Portfolio Overview")
        st.markdown(CSS_STYLES, unsafe_allow_html=True)

        if self.aggregated_shares.empty:
            st.info("No share data available for selected tickers.")
            return

        tiles_html = self._generate_tiles_html()
        st.html(f'<div class="tiles-container">{tiles_html}</div>')

    def _generate_tiles_html(self) -> str:
        """Generate HTML for all metric tiles."""
        return "".join(
            self._create_tile_html(row["Ticker"], row["Shares"])
            for _, row in self.aggregated_shares.iterrows()
        )

    def _create_tile_html(self, ticker: str, shares: float) -> str:
        """Create HTML for a single metric tile."""
        color = random.choice(BASE_COLORS) if BASE_COLORS else "#636EFA"
        gradient_color = adjust_gradient(color)
        text_color = determine_text_color_for_dropdown(color)
        formatted_shares = f"{shares:,.0f}" if pd.notna(shares) else "N/A"

        return f"""
        <div class="gradient-tile" style="
            background: linear-gradient(145deg, {color} 0%, {gradient_color} 100%);
            border-radius: 15px; padding: 1.5rem; margin: 1rem;
            color: {text_color}; box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            min-width: 250px; transition: all 0.3s ease;
            position: relative; overflow: hidden;
        ">
            <div style="
                position: absolute; top: -20px; right: -20px;
                width: 60px; height: 60px;
                background: {gradient_color}40; border-radius: 50%;
            "></div>
            <h3 style="margin:0; font-size:1.5rem; position: relative; font-weight:600;">
                {ticker}
            </h3>
            <p style="font-size:2.5rem; margin:0.5rem 0; font-weight:800; position: relative;">
                {formatted_shares}<span style="font-size:1rem; font-weight:500;"> shares</span>
            </p>
        </div>
        """

    def _render_charts_section(self) -> None:
        """Render the charts section."""
        st.markdown("## Dividend Analysis")

        if not self._has_dividend_data():
            st.info("No dividend data available for selected tickers.")
            return

        chart_data = self._prepare_chart_data()
        self._render_bar_chart(chart_data)
        self._render_pie_chart(chart_data)

    def _has_dividend_data(self) -> bool:
        """Check if filtered data has dividend information."""
        return (
            not self.filtered_df.empty
            and "Net Dividend" in self.filtered_df.columns
            and self.filtered_df["Net Dividend"].notna().any()
        )

    def _prepare_chart_data(self) -> pd.DataFrame:
        """Prepare aggregated data for charts."""
        return self.filtered_df.groupby("Ticker", as_index=False)[
            "Net Dividend"
        ].sum().sort_values("Ticker").reset_index(drop=True)

    def _render_bar_chart(self, chart_data: pd.DataFrame) -> None:
        """Render the dividend bar chart."""
        fig_bar = px.bar(
            chart_data,
            x="Ticker",
            y="Net Dividend",
            color="Ticker",
            title="Total Net Dividends by Ticker",
            color_discrete_map=self.ticker_colors,
        )
        fig_bar.update_layout(
            xaxis_title="Ticker",
            yaxis_title="Total Net Dividend (USD)",
            hovermode="x unified",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    def _render_pie_chart(self, chart_data: pd.DataFrame) -> None:
        """Render the dividend pie chart."""
        st.markdown(
            "<h3 style='font-size:17px; font-weight:bold;'>Dividend Distribution</h3>",
            unsafe_allow_html=True,
        )

        nivo_data = [
            {
                "id": row["Ticker"],
                "label": row["Ticker"],
                "value": row["Net Dividend"],
            }
            for _, row in chart_data.iterrows()
        ]

        nivo_chart = NivoPieChart(nivo_data, colors=self.ticker_colors)
        nivo_chart.render()

    def _render_calculator_section(self) -> None:
        """Render the dividend growth calculator section."""
        st.markdown("---")
        st.subheader("Dividend Growth Calculator")
        st.write("Project future dividend income based on growth assumptions.")

        if self.filtered_df.empty:
            st.warning("Please select tickers with data to use the calculator.")
            return

        self._render_calculator_inputs()
        self._render_projection_chart()

    def _render_calculator_inputs(self) -> None:
        """Render calculator input controls."""
        available_tickers = sorted(self.filtered_df["Ticker"].unique())

        if not available_tickers:
            st.warning("No tickers available for calculation.")
            return

        col1, col2 = st.columns(2)

        with col1:
            self.selected_ticker = st.selectbox(
                "Select company for projection:",
                available_tickers,
                index=0,
                key="calculator_ticker_select",
            )

        with col2:
            self.growth_percentage = st.number_input(
                "Annual dividend growth (%)",
                min_value=0.0,
                step=0.1,
                value=DEFAULT_GROWTH_PERCENTAGE,
                format="%.1f",
                key="calculator_growth_input",
            )

        self.num_years = st.slider(
            "Projection years",
            min_value=1,
            max_value=30,
            value=DEFAULT_NUM_YEARS,
            key="calculator_years_slider",
        )

    def _render_projection_chart(self) -> None:
        """Render the dividend projection chart."""
        if not self.selected_ticker:
            st.info("Select a ticker to see the projection.")
            return

        initial_dividend = self._get_initial_dividend()
        if initial_dividend is None:
            return

        projection_data = self._calculate_projection(initial_dividend)
        self._display_projection_chart(projection_data, initial_dividend)

    def _get_initial_dividend(self) -> Optional[float]:
        """Get the initial dividend for the selected ticker."""
        ticker_data = self.filtered_df[
            self.filtered_df["Ticker"] == self.selected_ticker
        ]

        if ticker_data.empty:
            st.warning(f"No data found for {self.selected_ticker}")
            return None

        if not self._has_valid_dividend_data(ticker_data):
            st.warning(f"No valid dividend data for {self.selected_ticker}")
            return None

        initial_dividend_series = ticker_data["Net Dividend"].dropna()
        if initial_dividend_series.empty:
            st.warning(f"No valid dividend found for {self.selected_ticker}")
            return None

        initial_dividend = initial_dividend_series.iloc[0]
        if initial_dividend <= 0:
            st.warning(f"Invalid dividend amount ({initial_dividend:.2f} USD)")
            return None

        return initial_dividend

    def _has_valid_dividend_data(self, ticker_data: pd.DataFrame) -> bool:
        """Check if ticker data has valid dividend information."""
        return (
            "Net Dividend" in ticker_data.columns
            and not ticker_data["Net Dividend"].isnull().all()
        )

    def _calculate_projection(self, initial_dividend: float) -> pd.DataFrame:
        """Calculate dividend projection data."""
        current_year = pd.Timestamp.now().year
        years = list(range(current_year, current_year + self.num_years))

        projected_dividends = [
            initial_dividend * (1 + self.growth_percentage / 100) ** i
            for i in range(self.num_years)
        ]

        return pd.DataFrame({
            "Year": years,
            "Projected Dividend (USD)": projected_dividends,
            "Ticker": [self.selected_ticker] * self.num_years,
        })

    def _display_projection_chart(
        self, projected_df: pd.DataFrame, initial_dividend: float
    ) -> None:
        """Display the projection chart with trend line."""
        chart_color = self.ticker_colors.get(
            self.selected_ticker, COLOR_THEME["fallback"]
        )

        fig_projected = px.bar(
            projected_df,
            x="Year",
            y="Projected Dividend (USD)",
            title=f"Projected Dividends for {self.selected_ticker} "
            f"(Starting: ${initial_dividend:.2f})",
            color_discrete_sequence=[chart_color],
        )

        # Add trend line
        fig_projected.add_scatter(
            x=projected_df["Year"],
            y=projected_df["Projected Dividend (USD)"],
            mode="lines+markers",
            name="Projected Trend",
            line=dict(color=COLOR_THEME["primary"], width=2, dash="dot"),
            marker=dict(size=5),
        )

        fig_projected.update_layout(
            xaxis_title="Year",
            yaxis_title="Projected Dividend (USD)",
            hovermode="x unified",
        )

        st.plotly_chart(fig_projected, use_container_width=True)


def main() -> None:
    """Main entry point for the application."""
    app = DividendApp()
    app.run()


if __name__ == "__main__":
    main()
