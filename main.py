import pandas as pd
import plotly.express as px
import streamlit as st
from app.app_config import (
    COLOR_THEME,
    DATA_FILE_PATH,
    DEFAULT_GROWTH_PERCENTAGE,
    DEFAULT_LAYOUT,
    DEFAULT_NUM_YEARS,
    DEFAULT_PAGE_TITLE,
    DEFAULT_SIDEBAR_STATE,
)
from app.components.drip_calculator import DRIPCalculator
from app.components.nivo_pie_chart import NivoPieChart
from app.data_processor import DividendDataProcessor
from app.styles.colors_and_styles import CSS_STYLES
from app.utils.color_manager import ColorManager
from app.utils.dividend_calculator import DividendCalculator


class DividendApp:
    """Streamlit-based dividend portfolio dashboard.

    Orchestrates data loading, ticker filtering, color assignment,
    and rendering of all UI sections: portfolio overview, distribution
    breakdown, growth calculator, and DRIP simulation.
    """

    def __init__(self) -> None:
        """Configure the Streamlit page and initialize core collaborators.

        Sets page title, layout, and sidebar state, then loads portfolio
        data and prepares `color_manager`, `calculator`, and application
        state attributes.
        """
        st.set_page_config(
            page_title=DEFAULT_PAGE_TITLE,
            initial_sidebar_state=DEFAULT_SIDEBAR_STATE,
            layout=DEFAULT_LAYOUT,
        )

        self.data_processor = self._load_data()
        self.color_manager = ColorManager()
        self.calculator = DividendCalculator()

        # Application state
        self.filtered_df = pd.DataFrame()
        self.selected_tickers: list[str] = []
        self.selected_ticker: str | None = None

    def _load_data(self) -> DividendDataProcessor:
        """Load the portfolio TSV and return a DividendDataProcessor.

        Returns:
            An initialized DividendDataProcessor backed by DATA_FILE_PATH.

        Raises:
            SystemExit: Calls st.stop() if the file cannot be loaded.
        """
        try:
            return DividendDataProcessor(DATA_FILE_PATH)
        except Exception as e:
            st.error(f"Failed to load data: {e}")
            st.stop()

    def run(self) -> None:
        """Run the full application rendering sequence.

        Renders the page title, ticker selector, and all dashboard
        sections in order.
        """
        st.title("Dividend Analysis Dashboard")

        self._render_ticker_selector()
        self._process_data()
        self._render_dashboard()

    def _render_ticker_selector(self) -> None:
        """Render the multiselect widget for choosing portfolio tickers.

        Populates `self.selected_tickers` with the user's selection.
        Displays a warning and returns early if no data is loaded.
        """
        if self.data_processor.df is None or self.data_processor.df.empty:
            st.warning("No data available.")
            return

        all_tickers = sorted(self.data_processor.df["Ticker"].unique())
        self.selected_tickers = st.multiselect(
            "Select tickers to analyze:",
            options=all_tickers,
            default=all_tickers,
            help="Choose stock tickers for analysis",
        )

    def _process_data(self) -> None:
        """Filter portfolio data to the selected tickers and assign colors.

        Updates `self.filtered_df` with rows matching `self.selected_tickers`
        and calls `color_manager.generate_colors_for_tickers` for the
        resulting unique tickers. Resets `filtered_df` to an empty DataFrame
        if no tickers are selected.
        """
        if not self.selected_tickers:
            self.filtered_df = pd.DataFrame()
            return

        self.filtered_df = self.data_processor.filter_data(self.selected_tickers)

        # Convert numpy array to list to avoid ambiguous truth value errors
        unique_tickers = list(self.filtered_df["Ticker"].unique()) if not self.filtered_df.empty else []
        self.color_manager.generate_colors_for_tickers(unique_tickers)

    def _render_dashboard(self) -> None:
        """Render all dashboard sections if filtered data is available.

        Renders portfolio overview, distribution breakdown, growth
        calculator, and DRIP simulation in sequence. Displays an info
        message and returns early when `filtered_df` is empty.
        """
        if self.filtered_df.empty:
            st.info("Select tickers to view analysis.")
            return

        self._render_portfolio_overview()
        self._render_dividend_analysis()
        self._render_calculator()
        self._render_drip_calculator()

    def _render_portfolio_overview(self) -> None:
        """Render gradient HTML tiles showing total shares per ticker.

        Groups `filtered_df` by ticker, sums shares, and renders one
        gradient tile per ticker via `ColorManager.create_tile_html`.
        """
        st.markdown("## Portfolio Overview")
        st.markdown(CSS_STYLES, unsafe_allow_html=True)

        if "Shares" not in self.filtered_df.columns:
            st.info("No share data available.")
            return

        # Aggregate shares by ticker
        aggregated = self.filtered_df.groupby("Ticker", as_index=False)["Shares"].sum()

        tiles_html = "".join(
            self.color_manager.create_tile_html(row["Ticker"], row["Shares"]) for _, row in aggregated.iterrows()
        )

        st.html(f'<div class="tiles-container">{tiles_html}</div>')

    def _render_dividend_analysis(self) -> None:
        """Render a Nivo.js donut chart of net dividend distribution.

        Groups `filtered_df` by ticker, sums net dividends, and passes
        the aggregated data to `NivoPieChart` for rendering.
        """
        st.markdown("## Distribution Breakdown")
        st.caption("View the distribution of received dividend payments across portfolio")

        if "Net Dividend" not in self.filtered_df.columns:
            st.info("No dividend data available.")
            return

        # Prepare chart data
        chart_data = self.filtered_df.groupby("Ticker", as_index=False)["Net Dividend"].sum().sort_values("Ticker")

        # Pie chart
        nivo_data = [
            {"id": row["Ticker"], "label": row["Ticker"], "value": row["Net Dividend"]}
            for _, row in chart_data.iterrows()
        ]
        NivoPieChart(nivo_data, colors=self.color_manager.ticker_colors, height=400).render()

    def _render_calculator(self) -> None:
        """Render the dividend growth calculator section.

        Provides controls for ticker selection, annual growth rate, and
        projection horizon, then delegates to `_show_projection` to
        display the resulting chart and metrics.
        """
        st.header("Dividend Growth Calculator")
        st.caption("Project future dividend income based on growth assumptions.")

        available_tickers = sorted(self.filtered_df["Ticker"].unique())
        if not available_tickers:
            st.warning("No tickers available for calculation.")
            return

        # Input controls
        col1, col2 = st.columns(2)

        with col1:
            self.selected_ticker = st.selectbox("Select company:", available_tickers, key="calc_ticker")

        with col2:
            growth_rate = st.number_input(
                "Annual growth (%)",
                min_value=0,
                max_value=100,
                step=1,
                value=int(DEFAULT_GROWTH_PERCENTAGE),
                format="%d",
                key="calc_growth",
            )

        years = st.slider(
            "Projection years",
            min_value=1,
            max_value=30,
            value=DEFAULT_NUM_YEARS,
            key="calc_years",
        )

        # Calculate and display projections
        if self.selected_ticker:
            self._show_projection(growth_rate, years)

    def _show_projection(self, growth_rate: float, years: int) -> None:
        """Render growth metrics and a bar chart for the selected ticker.

        Calculates year-by-year dividend projections and highlights bars
        where the projected dividend crosses a doubling threshold (2x, 4x,
        and so on) using COLOR_THEME["primary"].

        Args:
            growth_rate: Expected annual dividend growth as a percentage
                (for example, 5 for 5%).
            years: Number of years to project forward.
        """
        ticker_data = self.filtered_df[self.filtered_df["Ticker"] == self.selected_ticker]

        initial_dividend = self.calculator.get_initial_dividend(ticker_data)
        if initial_dividend is None:
            st.warning(f"No valid dividend data for {self.selected_ticker}")
            return

        # Get currency symbol
        currency = self.calculator.get_currency_symbol(self.selected_ticker)

        # Calculate projections
        projections = self.calculator.calculate_projections(initial_dividend, growth_rate, years)

        # Calculate growth info
        growth_info = self.calculator.calculate_growth_info(initial_dividend, growth_rate, years)

        # Display growth metrics
        st.subheader("Growth Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Starting Dividend", value=f"{currency}{initial_dividend:.2f}")
        with col2:
            st.metric(
                label=f"Dividend After {years} Years",
                value=f"{currency}{growth_info['final_dividend']:.2f}",
                delta=f"+{growth_info['total_growth_pct']:.1f}%",
            )
        with col3:
            st.metric(
                label="Total Increase",
                value=f"{currency}{growth_info['total_increase']:.2f}",
            )

        # Create chart with color coding for doubling milestones
        chart_color = self.color_manager.ticker_colors.get(self.selected_ticker, COLOR_THEME["fallback"])

        # Mark years where dividend crosses doubling thresholds (2x, 4x, 8x, etc.)
        bar_colors = []
        multipliers = [2, 4, 8, 16, 32, 64]
        prev_value = 0

        for current_value in projections["Projected Dividend"]:
            # Check if we crossed any threshold between prev and current value
            is_milestone = any(prev_value < initial_dividend * m <= current_value for m in multipliers)
            bar_colors.append(COLOR_THEME["primary"] if is_milestone else chart_color)
            prev_value = current_value

        fig = px.bar(
            projections,
            x="Year",
            y="Projected Dividend",
            title=f"Projected Dividends for {self.selected_ticker} (Starting: {currency}{initial_dividend:.2f})",
        )

        # Update bar colors
        fig.update_traces(marker_color=bar_colors)

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
        fig.update_traces(selector=dict(type="bar"), width=0.8)

        st.plotly_chart(fig, use_container_width=True)

    def _render_drip_calculator(self) -> None:
        """Render the DRIP (Dividend Reinvestment Plan) calculator section.

        Instantiates `DRIPCalculator` with the current ticker colors and
        calls its `render` method.
        """
        st.markdown("## DRIP Calculator")
        st.caption("Simulate dividend reinvestment to estimate compound growth over time")

        drip_calc = DRIPCalculator(self.color_manager.ticker_colors)
        drip_calc.render()


def main() -> None:
    """Instantiate and run the dividend dashboard application."""
    app = DividendApp()
    app.run()


if __name__ == "__main__":
    main()
