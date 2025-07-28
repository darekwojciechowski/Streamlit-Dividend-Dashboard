"""Color management utilities for the dividend dashboard."""

import random
import pandas as pd
import plotly.express as px
from styles.colors_and_styles import BASE_COLORS, adjust_gradient, determine_text_color_for_dropdown


class ColorManager:
    """Manages color assignment and generation for tickers."""

    def __init__(self):
        self.ticker_colors = {}

    def generate_colors_for_tickers(self, tickers: list) -> dict:
        """Generate consistent colors for a list of tickers."""
        if not tickers:
            return {}

        unique_tickers = sorted(tickers)
        color_palette = px.colors.qualitative.Pastel

        self.ticker_colors = {
            ticker: color_palette[i % len(color_palette)]
            for i, ticker in enumerate(unique_tickers)
        }
        return self.ticker_colors

    def get_random_base_color(self) -> str:
        """Get a random color from base colors."""
        return random.choice(BASE_COLORS) if BASE_COLORS else "#636EFA"

    def create_tile_html(self, ticker: str, shares: float) -> str:
        """Create HTML for a metric tile."""
        color = self.get_random_base_color()
        gradient_color = adjust_gradient(color)
        text_color = determine_text_color_for_dropdown(color)
        formatted_shares = f"{shares:,.0f}" if pd.notna(
            shares) and shares > 0 else "N/A"

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
