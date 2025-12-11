"""Modern DRIP (Dividend Reinvestment Plan) Calculator Component."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List
from styles.colors_and_styles import CSS_STYLES


class DRIPCalculator:
    """Modern DRIP Calculator with advanced visualizations."""

    def __init__(self, ticker_colors: Dict[str, str]):
        """Initialize DRIP calculator."""
        self.ticker_colors = ticker_colors

    @staticmethod
    def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
        """
        Convert hex color to rgba string.

        Args:
            hex_color: Hex color string (e.g., '#3b82f6')
            alpha: Alpha transparency (0-1)

        Returns:
            RGBA color string
        """
        # Remove # if present
        hex_color = hex_color.lstrip('#')

        # Handle short form (e.g., #fff)
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])

        # Default to purple if invalid
        if len(hex_color) != 6:
            hex_color = '8A2BE2'

        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f'rgba({r}, {g}, {b}, {alpha})'
        except ValueError:
            return f'rgba(138, 43, 226, {alpha})'  # Default purple

    def calculate_drip(
        self,
        initial_shares: float,
        share_price: float,
        annual_dividend: float,
        dividend_growth: float,
        share_price_growth: float,
        years: int,
        payment_frequency: int = 4  # quarterly
    ) -> pd.DataFrame:
        """
        Calculate DRIP with reinvestment.

        Args:
            initial_shares: Starting number of shares
            share_price: Initial share price
            annual_dividend: Annual dividend per share
            dividend_growth: Annual dividend growth rate (%)
            share_price_growth: Annual share price growth rate (%)
            years: Number of years to project
            payment_frequency: Payments per year (4=quarterly, 12=monthly)
        """
        results = []
        current_shares = initial_shares
        current_price = share_price
        current_annual_div = annual_dividend

        for year in range(years + 1):
            # Store shares at the beginning of the year (before reinvestment)
            shares_start_of_year = current_shares
            price_start_of_year = current_price

            # Calculate dividend per payment
            dividend_per_payment = current_annual_div / payment_frequency

            # Reinvest dividends throughout the year
            shares_added = 0
            total_dividend = 0
            temp_shares = shares_start_of_year

            for payment_num in range(payment_frequency):
                # Calculate price at this payment point (linear interpolation through the year)
                price_fraction = (payment_num + 0.5) / \
                    payment_frequency  # Mid-point of period
                price_growth_factor = (1 + share_price_growth / 100)
                price_at_payment = max(
                    price_start_of_year * (price_growth_factor ** price_fraction), 0.01)

                # Calculate dividend payment based on current shares (including previously reinvested)
                payment = temp_shares * dividend_per_payment
                total_dividend += payment

                new_shares = payment / price_at_payment
                shares_added += new_shares
                temp_shares += new_shares

            # Update current shares after all reinvestments
            current_shares = temp_shares

            # Price at END of year (after full year's growth)
            price_end_of_year = max(
                price_start_of_year * (1 + share_price_growth / 100), 0.01)

            # Portfolio value at END of year (after reinvestment, at end-of-year price)
            portfolio_value = current_shares * price_end_of_year

            # Calculate what value would be without DRIP (at end-of-year price)
            value_without_drip = initial_shares * price_end_of_year
            drip_benefit = portfolio_value - value_without_drip

            results.append({
                'Year': pd.Timestamp.now().year + year,
                'Shares': current_shares,
                'Shares Added': shares_added,
                'Share Price': price_end_of_year,
                'Annual Dividend': current_annual_div,
                'Total Dividend Income': total_dividend,
                'Portfolio Value': portfolio_value,
                'Value Without DRIP': value_without_drip,
                'DRIP Benefit': drip_benefit
            })

            # Update for next year
            current_price = price_end_of_year
            current_annual_div *= (1 + dividend_growth / 100)

        return pd.DataFrame(results)

    def render_modern_chart(
        self,
        df: pd.DataFrame,
        ticker: str,
        currency: str = "$"
    ) -> None:
        """Render modern, interactive DRIP visualization."""

        # Create subplot with secondary y-axis
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Portfolio Value Growth',
                'DRIP vs No Reinvestment',
                'Share Accumulation',
                'Annual Dividend Income'
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )

        color = self.ticker_colors.get(ticker, "#8A2BE2")

        # Convert color to rgba for fills (WCAG compliant alpha values)
        fill_color = self.hex_to_rgba(color, 0.5)
        fill_color_strong = self.hex_to_rgba(color, 0.6)

        # 1. Portfolio Value Growth (with gradient fill)
        fig.add_trace(
            go.Scatter(
                x=df['Year'],
                y=df['Portfolio Value'],
                name='Portfolio Value',
                mode='lines',
                line=dict(color=color, width=3),
                fill='tozeroy',
                fillcolor=fill_color,
                hovertemplate=f'<b>Year: %{{x}}</b><br>Value: {currency}%{{y:,.2f}}<extra></extra>'
            ),
            row=1, col=1
        )

        # 2. DRIP Benefit Comparison
        fig.add_trace(
            go.Scatter(
                x=df['Year'],
                y=df['Value Without DRIP'],
                name='Without DRIP',
                mode='lines',
                line=dict(color=self.hex_to_rgba(
                    color, 0.6), width=2, dash='dash'),
                hovertemplate=f'<b>Year: %{{x}}</b><br>Value: {currency}%{{y:,.2f}}<extra></extra>'
            ),
            row=1, col=2
        )

        fig.add_trace(
            go.Scatter(
                x=df['Year'],
                y=df['Portfolio Value'],
                name='With DRIP',
                mode='lines',
                line=dict(color=color, width=3),
                fill='tonexty',
                fillcolor=fill_color_strong,
                hovertemplate=f'<b>Year: %{{x}}</b><br>Value: {currency}%{{y:,.2f}}<extra></extra>'
            ),
            row=1, col=2
        )

        # 3. Share Accumulation (Bar chart)
        fig.add_trace(
            go.Bar(
                x=df['Year'],
                y=df['Shares'],
                name='Total Shares',
                marker=dict(
                    color=df['Shares'],
                    colorscale=[[0, self.hex_to_rgba(color, 0.6)], [1, color]],
                    showscale=False
                ),
                hovertemplate='<b>Year: %{x}</b><br>Shares: %{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )

        # 4. Annual Dividend Income (Area chart)
        fig.add_trace(
            go.Scatter(
                x=df['Year'],
                y=df['Total Dividend Income'],
                name='Dividend Income',
                mode='lines',
                line=dict(color=color, width=3),
                fill='tozeroy',
                fillcolor=fill_color,
                hovertemplate=f'<b>Year: %{{x}}</b><br>Income: {currency}%{{y:,.2f}}<extra></extra>'
            ),
            row=2, col=2
        )

        # Update layout for modern look
        fig.update_layout(
            height=700,
            showlegend=False,
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter, system-ui, sans-serif',
                      size=12, color='#e5e7eb'),
            margin=dict(t=70, l=40, r=40, b=40),
            hoverlabel=dict(
                bgcolor='rgba(30, 30, 30, 0.95)',
                font_size=13,
                font_family='Inter, system-ui, sans-serif',
                font_color='#e5e7eb',
                bordercolor='rgba(148, 163, 184, 0.3)'
            )
        )

        # Update subplot titles with modern styling
        for annotation in fig.layout.annotations:
            annotation.update(
                font=dict(size=15, color='#f3f4f6',
                          family='Inter, system-ui, sans-serif', weight=600),
                xanchor='center',
                x=annotation.x
            )

        # Update all axes for minimal, modern style
        fig.update_xaxes(
            showgrid=False,
            showline=False,
            tickfont=dict(size=11, color='#9ca3af'),
            zeroline=False
        )

        fig.update_yaxes(
            showgrid=False,
            showline=False,
            tickfont=dict(size=11, color='#9ca3af'),
            zeroline=False
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_metrics_cards(
        self,
        df: pd.DataFrame,
        currency: str = "$"
    ) -> None:
        """Render modern metric cards."""

        initial = df.iloc[0]
        final = df.iloc[-1]

        # Calculate key metrics
        initial_investment = initial['Portfolio Value']
        total_return = ((final['Portfolio Value'] - initial_investment) /
                        initial_investment * 100)
        drip_advantage = ((final['Portfolio Value'] - final['Value Without DRIP']) /
                          final['Value Without DRIP'] * 100)
        total_shares_gained = final['Shares'] - initial['Shares']
        # Sum all dividend income across all years
        total_dividends = df['Total Dividend Income'].sum()

        # Format return values with proper sign handling
        total_return_formatted = f"{total_return:+.0f}%" if total_return != 0 else "0%"
        drip_advantage_formatted = f"{drip_advantage:+.0f}%" if drip_advantage != 0 else "0%"

        # Use CSS styles from colors_and_styles module
        st.markdown(CSS_STYLES, unsafe_allow_html=True)

        cols = st.columns(4)

        metrics = [
            {
                'label': 'Total Return',
                'value': total_return_formatted,
                'delta': f'{currency}{final["Portfolio Value"]:,.0f}',
                'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            },
            {
                'label': 'DRIP Advantage',
                'value': drip_advantage_formatted,
                'delta': f'{currency}{final["DRIP Benefit"]:,.0f} extra',
                'gradient': 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)'
            },
            {
                'label': 'Shares Gained',
                'value': f'{total_shares_gained:.0f}',
                'delta': f'{(total_shares_gained/initial["Shares"]*100):.0f}% increase',
                'gradient': 'linear-gradient(135deg, #0575e6 0%, #021b79 100%)'
            },
            {
                'label': 'Total Dividends',
                'value': f'{currency}{total_dividends:,.0f}',
                'delta': f'{len(df) - 1} years projected',
                'gradient': 'linear-gradient(135deg, #56ab2f 0%, #a8e063 100%)'
            }
        ]

        for col, metric in zip(cols, metrics):
            with col:
                st.markdown(f"""
                <div class="metric-card" style="background: {metric['gradient']};">
                    <div class="metric-label">{metric['label']}</div>
                    <div class="metric-value">{metric['value']}</div>
                    <div class="metric-delta">{metric['delta']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

    def render(
        self,
        filtered_df: pd.DataFrame,
        ticker_colors: Dict[str, str]
    ) -> None:
        """Render complete modern DRIP calculator interface."""

        col1, col2, col3 = st.columns(3)

        with col1:
            selected_ticker = st.text_input(
                "Select Ticker",
                value="",
                placeholder="Enter ticker symbol (e.g., KO)",
                key="drip_ticker",
                help="Enter any ticker symbol (e.g., KO)"
            )

            initial_shares = st.number_input(
                "Initial Shares",
                min_value=1,
                value=25,
                step=1,
                format="%d",
                key="drip_shares"
            )

        with col2:
            share_price = st.number_input(
                "Current Share Price ($)",
                min_value=1,
                value=100,
                step=1,
                format="%d",
                key="drip_price"
            )

            annual_dividend = st.number_input(
                "Annual Dividend/Share ($)",
                min_value=0,
                value=3,
                step=1,
                format="%d",
                key="drip_dividend"
            )

        with col3:
            dividend_growth = st.slider(
                "Dividend Growth (%/year)",
                min_value=0,
                max_value=20,
                value=6,
                key="drip_div_growth"
            )

            share_price_growth = st.slider(
                "Share Price Growth (%/year)",
                min_value=0,
                max_value=20,
                value=4,
                key="drip_price_growth"
            )

        col4, col5 = st.columns(2)
        with col4:
            frequency = st.selectbox(
                "Payment Frequency",
                options=[12, 4, 2, 1],
                format_func=lambda x: {
                    12: "Monthly",
                    4: "Quarterly",
                    2: "Semi-annually",
                    1: "Annually"
                }[x],
                index=1,  # Default to Quarterly
                key="drip_frequency"
            )

        with col5:
            years = st.slider(
                "Projection Period (years)",
                min_value=0,
                max_value=30,
                value=15,
                key="drip_years"
            )

        # Calculate DRIP
        df = self.calculate_drip(
            initial_shares=initial_shares,
            share_price=share_price,
            annual_dividend=annual_dividend,
            dividend_growth=dividend_growth,
            share_price_growth=share_price_growth,
            years=years,
            payment_frequency=frequency
        )

        # Get currency
        currency = "$"
        if "." in selected_ticker:
            country_code = selected_ticker.split(".")[-1]
            currency = "PLN" if country_code == "PL" else "$"

        # Render metrics cards
        self.render_metrics_cards(df, currency)

        # Render charts
        self.render_modern_chart(df, selected_ticker, currency)
