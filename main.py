from typing import Dict, List, Optional
import streamlit as st
import pandas as pd
import plotly.express as px

from data_processor import DividendDataProcessor
from components.nivo_pie_chart import NivoPieChart
from components.drip_calculator import DRIPCalculator
from utils.color_manager import ColorManager
from utils.dividend_calculator import DividendCalculator
from styles.colors_and_styles import CSS_STYLES
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
    """Modern Streamlit Dividend Dashboard Application."""

    def __init__(self) -> None:
        """Initialize the application."""
        st.set_page_config(
            page_title=DEFAULT_PAGE_TITLE,
            initial_sidebar_state=DEFAULT_SIDEBAR_STATE,
            layout=DEFAULT_LAYOUT
        )

        self.data_processor = self._load_data()
        self.color_manager = ColorManager()
        self.calculator = DividendCalculator()

        # Application state
        self.filtered_df = pd.DataFrame()
        self.selected_tickers: List[str] = []
        self.selected_ticker: Optional[str] = None

    def _load_data(self) -> DividendDataProcessor:
        """Load and initialize data processor."""
        try:
            return DividendDataProcessor(DATA_FILE_PATH)
        except Exception as e:
            st.error(f"Failed to load data: {e}")
            st.stop()

    def run(self) -> None:
        """Main application flow."""
        st.title("Dividend Analysis Dashboard")

        self._render_ticker_selector()
        self._process_data()
        self._render_dashboard()

    def _render_ticker_selector(self) -> None:
        """Render the ticker selection widget."""
        if self.data_processor.df is None or self.data_processor.df.empty:
            st.warning("No data available.")
            return

        all_tickers = sorted(self.data_processor.df["Ticker"].unique())
        self.selected_tickers = st.multiselect(
            "Select tickers to analyze:",
            options=all_tickers,
            default=all_tickers,
            help="Choose stock tickers for analysis"
        )

    def _process_data(self) -> None:
        """Process and filter data based on selections."""
        if not self.selected_tickers:
            self.filtered_df = pd.DataFrame()
            return

        self.filtered_df = self.data_processor.filter_data(
            self.selected_tickers)

        # Convert numpy array to list to avoid ambiguous truth value errors
        unique_tickers = list(
            self.filtered_df["Ticker"].unique()) if not self.filtered_df.empty else []
        self.color_manager.generate_colors_for_tickers(unique_tickers)

    def _render_dashboard(self) -> None:
        """Render the main dashboard components."""
        if self.filtered_df.empty:
            st.info("Select tickers to view analysis.")
            return

        self._render_portfolio_overview()
        self._render_dividend_analysis()
        self._render_calculator()
        self._render_drip_calculator()

    def _render_portfolio_overview(self) -> None:
        """Render portfolio overview with share metrics."""
        st.markdown("## Portfolio Overview")
        st.markdown(CSS_STYLES, unsafe_allow_html=True)

        if "Shares" not in self.filtered_df.columns:
            st.info("No share data available.")
            return

        # Aggregate shares by ticker
        aggregated = self.filtered_df.groupby(
            "Ticker", as_index=False)["Shares"].sum()

        tiles_html = "".join(
            self.color_manager.create_tile_html(row["Ticker"], row["Shares"])
            for _, row in aggregated.iterrows()
        )

        st.html(f'<div class="tiles-container">{tiles_html}</div>')

    def _render_dividend_analysis(self) -> None:
        """Render dividend analysis charts."""
        st.markdown("## Distribution Breakdown")
        st.caption(
            "View the distribution of received dividend payments across portfolio")

        if "Net Dividend" not in self.filtered_df.columns:
            st.info("No dividend data available.")
            return

        # Prepare chart data
        chart_data = (self.filtered_df
                      .groupby("Ticker", as_index=False)["Net Dividend"]
                      .sum()
                      .sort_values("Ticker"))

        # Pie chart
        nivo_data = [
            {"id": row["Ticker"], "label": row["Ticker"],
                "value": row["Net Dividend"]}
            for _, row in chart_data.iterrows()
        ]
        NivoPieChart(
            nivo_data, colors=self.color_manager.ticker_colors, height=400).render()

    def _render_calculator(self) -> None:
        """Render dividend growth calculator."""
        st.header("Dividend Growth Calculator")
        st.caption("Project future dividend income based on growth assumptions.")

        available_tickers = sorted(self.filtered_df["Ticker"].unique())
        if not available_tickers:
            st.warning("No tickers available for calculation.")
            return

        # Input controls
        col1, col2 = st.columns(2)

        with col1:
            self.selected_ticker = st.selectbox(
                "Select company:",
                available_tickers,
                key="calc_ticker"
            )

        with col2:
            growth_rate = st.number_input(
                "Annual growth (%)",
                min_value=0,
                max_value=100,
                step=1,
                value=int(DEFAULT_GROWTH_PERCENTAGE),
                format="%d",
                key="calc_growth"
            )

        years = st.slider(
            "Projection years",
            min_value=1,
            max_value=30,
            value=DEFAULT_NUM_YEARS,
            key="calc_years"
        )

        # Calculate and display projections
        if self.selected_ticker:
            self._show_projection(growth_rate, years)

    def _show_projection(self, growth_rate: float, years: int) -> None:
        """Show dividend projections for selected ticker."""
        ticker_data = self.filtered_df[
            self.filtered_df["Ticker"] == self.selected_ticker
        ]

        initial_dividend = self.calculator.get_initial_dividend(ticker_data)
        if initial_dividend is None:
            st.warning(f"No valid dividend data for {self.selected_ticker}")
            return

        # Get currency symbol
        currency = self.calculator.get_currency_symbol(self.selected_ticker)

        # Calculate projections
        projections = self.calculator.calculate_projections(
            initial_dividend, growth_rate, years
        )

        # Calculate growth info
        growth_info = self.calculator.calculate_growth_info(
            initial_dividend, growth_rate, years
        )

        # Display growth metrics
        st.subheader("Growth Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label=f"Starting Dividend",
                value=f"{currency}{initial_dividend:.2f}"
            )
        with col2:
            st.metric(
                label=f"Dividend After {years} Years",
                value=f"{currency}{growth_info['final_dividend']:.2f}",
                delta=f"+{growth_info['total_growth_pct']:.1f}%"
            )
        with col3:
            st.metric(
                label="Total Increase",
                value=f"{currency}{growth_info['total_increase']:.2f}"
            )

        # Create chart with color coding for doubling milestones
        chart_color = self.color_manager.ticker_colors.get(
            self.selected_ticker, COLOR_THEME["fallback"]
        )

        # Mark only the specific years where dividend crosses doubling thresholds (2x, 4x, 8x, etc.)
        projections['Milestone'] = 'Normal'

        for i in range(len(projections)):
            current_value = projections.iloc[i]['Projected Dividend']

            # Check if this is the first year to cross each doubling threshold
            for multiplier in [2, 4, 8, 16, 32, 64]:
                threshold = initial_dividend * multiplier

                # Check if current value crosses threshold
                if current_value >= threshold:
                    # Check if previous value was below threshold (first crossing)
                    if i == 0 or projections.iloc[i-1]['Projected Dividend'] < threshold:
                        projections.loc[projections.index[i],
                                        'Milestone'] = 'Doubled'
                        break

        fig = px.bar(
            projections,
            x="Year",
            y="Projected Dividend",
            color="Milestone",
            title=f"Projected Dividends for {self.selected_ticker} "
            f"(Starting: {currency}{initial_dividend:.2f})",
            color_discrete_map={
                'Normal': chart_color,
                # Use theme color for doubling milestones
                'Doubled': COLOR_THEME["primary"]
            },
        )

        # Add trend line
        fig.add_scatter(
            x=projections["Year"],
            y=projections["Projected Dividend"],
            mode="lines+markers",
            name="Trend",
            line=dict(color=COLOR_THEME["primary"], width=2, dash="dot"),
        )

        fig.update_layout(
            xaxis_title="Year",
            yaxis_title=f"Projected Dividend ({currency})",
            hovermode="x unified",
            bargap=0.2,
        )

        # Set bar width only for bar traces
        fig.update_traces(selector=dict(type='bar'), width=0.8)

        st.plotly_chart(fig, use_container_width=True)

    def _render_drip_calculator(self) -> None:
        """Render modern DRIP calculator."""
        st.markdown("## DRIP Calculator")
        st.caption(
            "Simulate dividend reinvestment to estimate compound growth over time")

        drip_calc = DRIPCalculator(self.color_manager.ticker_colors)
        drip_calc.render(self.filtered_df, self.color_manager.ticker_colors)


def main() -> None:
    """Application entry point."""
    app = DividendApp()
    app.run()


if __name__ == "__main__":
    main()
