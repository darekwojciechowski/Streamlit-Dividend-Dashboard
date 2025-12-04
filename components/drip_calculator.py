"""Modern DRIP (Dividend Reinvestment Plan) Calculator Component."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List


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

        # Default to blue if invalid
        if len(hex_color) != 6:
            hex_color = '3b82f6'

        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f'rgba({r}, {g}, {b}, {alpha})'
        except ValueError:
            return f'rgba(59, 130, 246, {alpha})'  # Default blue

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
            # Calculate values for this year
            dividend_per_payment = current_annual_div / payment_frequency
            total_dividend = current_shares * current_annual_div

            # Reinvest dividends throughout the year
            shares_added = 0
            for _ in range(payment_frequency):
                payment = current_shares * dividend_per_payment
                new_shares = payment / current_price
                shares_added += new_shares
                current_shares += new_shares

            # Portfolio value
            portfolio_value = current_shares * current_price

            # Calculate what value would be without DRIP
            value_without_drip = initial_shares * current_price
            drip_benefit = portfolio_value - value_without_drip

            results.append({
                'Year': pd.Timestamp.now().year + year,
                'Shares': current_shares,
                'Shares Added': shares_added,
                'Share Price': current_price,
                'Annual Dividend': current_annual_div,
                'Total Dividend Income': total_dividend,
                'Portfolio Value': portfolio_value,
                'Value Without DRIP': value_without_drip,
                'DRIP Benefit': drip_benefit
            })

            # Update for next year
            current_price *= (1 + share_price_growth / 100)
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

        color = self.ticker_colors.get(ticker, "#3b82f6")

        # Convert color to rgba for fills
        fill_color = self.hex_to_rgba(color, 0.2)
        fill_color_strong = self.hex_to_rgba(color, 0.3)

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
                line=dict(color='#94a3b8', width=2, dash='dash'),
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
                    colorscale=[[0, self.hex_to_rgba(color, 0.4)], [1, color]],
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
                line=dict(color='#10b981', width=3),
                fill='tozeroy',
                fillcolor='rgba(16, 185, 129, 0.2)',
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
            font=dict(family='Inter, system-ui, sans-serif', size=12),
            margin=dict(t=60, l=20, r=20, b=20)
        )

        # Update all axes for minimal, modern style
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(148, 163, 184, 0.1)',
            showline=False
        )

        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(148, 163, 184, 0.1)',
            showline=False
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
        total_return = ((final['Portfolio Value'] - initial['Portfolio Value']) /
                        initial['Portfolio Value'] * 100)
        drip_advantage = ((final['Portfolio Value'] - final['Value Without DRIP']) /
                          final['Value Without DRIP'] * 100)
        total_shares_gained = final['Shares'] - initial['Shares']
        total_dividends = df['Total Dividend Income'].sum()

        # Custom CSS for modern cards
        st.markdown("""
        <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            padding: 24px;
            color: white;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-5px);
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            margin: 8px 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            word-wrap: break-word;
        }
        .metric-label {
            font-size: 0.875rem;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .metric-delta {
            font-size: 1rem;
            margin-top: 8px;
            opacity: 0.95;
        }
        </style>
        """, unsafe_allow_html=True)

        cols = st.columns(4)

        metrics = [
            {
                'label': 'Total Return',
                'value': f'{total_return:.0f}%',
                'delta': f'{currency}{final["Portfolio Value"]:,.0f}',
                'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            },
            {
                'label': 'DRIP Advantage',
                'value': f'+{drip_advantage:.0f}%',
                'delta': f'{currency}{final["DRIP Benefit"]:,.0f} extra',
                'gradient': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
            },
            {
                'label': 'Shares Gained',
                'value': f'{total_shares_gained:.0f}',
                'delta': f'{(total_shares_gained/initial["Shares"]*100):.0f}% increase',
                'gradient': 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)'
            },
            {
                'label': 'Total Dividends',
                'value': f'{currency}{total_dividends:,.0f}',
                'delta': f'{len(df)} years projected',
                'gradient': 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
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

        st.markdown("## DRIP Calculator")
        st.caption(
            "Simulate dividend reinvestment and watch your wealth compound")

        col1, col2, col3 = st.columns(3)

        with col1:
            selected_ticker = st.text_input(
                "Select Ticker",
                value="",
                placeholder="Enter ticker symbol (e.g., AAPL.US)",
                key="drip_ticker",
                help="Enter any ticker symbol (e.g., AAPL.US, MSFT.US)"
            )

            initial_shares = st.number_input(
                "Initial Shares",
                min_value=1,
                value=100,
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
                value=4,
                step=1,
                format="%d",
                key="drip_dividend"
            )

        with col3:
            dividend_growth = st.slider(
                "Dividend Growth (%/year)",
                min_value=0,
                max_value=20,
                value=5,
                key="drip_div_growth"
            )

            share_price_growth = st.slider(
                "Share Price Growth (%/year)",
                min_value=-10,
                max_value=30,
                value=8,
                key="drip_price_growth"
            )

        col4, col5 = st.columns(2)
        with col4:
            years = st.slider(
                "Projection Period (years)",
                min_value=0,
                max_value=30,
                value=20,
                key="drip_years"
            )

        with col5:
            frequency = st.selectbox(
                "Payment Frequency",
                options=[1, 4],
                format_func=lambda x: "Annually" if x == 1 else "Quarterly",
                key="drip_frequency"
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
