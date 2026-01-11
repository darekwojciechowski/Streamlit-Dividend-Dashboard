"""Color management utilities for the dividend dashboard."""

import random
import pandas as pd
import plotly.express as px
from styles.colors_and_styles import BASE_COLORS


def adjust_gradient(color: str) -> str:
    """
    Adjusts the input color to create a slightly lighter version for gradients.

    Args:
        color (str): The base color in hex (#RRGGBB) or rgb(r, g, b) format.

    Returns:
        str: The adjusted color in rgb(r, g, b) format.
    """
    try:
        if color.startswith('rgb'):
            # Extract numbers, handle potential alpha value if present
            rgb_values = color.split('(')[1].split(')')[0].split(',')
            rgb = [int(c.strip())
                   for c in rgb_values[:3]]  # Take only first 3 for RGB
        elif color.startswith('#'):
            hex_color = color.lstrip('#')
            if len(hex_color) == 3:  # Handle shorthand hex (e.g., #F00)
                hex_color = ''.join([c*2 for c in hex_color])
            if len(hex_color) != 6:
                raise ValueError("Invalid hex color format")
            rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        else:
            raise ValueError(
                "Invalid color format. Use #RRGGBB or rgb(r,g,b).")

        # Increase brightness slightly, capping at 255
        adjusted = [min(255, c + 40) for c in rgb]
        return f'rgb({adjusted[0]}, {adjusted[1]}, {adjusted[2]})'
    except Exception as e:
        print(f"Error adjusting gradient for color '{color}': {e}")
        # Return a default or the original color in case of error
        return 'rgb(200, 200, 200)'  # Default grey


def apply_wcag_ui_standards(color: str) -> bool:
    """
    Determine if a color is perceived as light or dark based on WCAG luminance.

    Used to decide contrasting text color (e.g., black text on light background).

    Args:
        color (str): Color in hex (#RRGGBB or #RGB) format.

    Returns:
        bool: True if the color is considered light (luminance > 0.5), False otherwise.
    """
    try:
        color = color.lstrip('#')
        if len(color) == 3:
            color = ''.join([c*2 for c in color])
        if len(color) != 6:
            raise ValueError("Invalid hex color format for WCAG check")

        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)

        # Calculate relative luminance (formula from WCAG 2.1)
        # Normalize RGB values to 0-1
        rgb = [x / 255.0 for x in (r, g, b)]
        # Apply gamma correction
        for i in range(3):
            if rgb[i] <= 0.03928:
                rgb[i] = rgb[i] / 12.92
            else:
                rgb[i] = ((rgb[i] + 0.055) / 1.055) ** 2.4
        # Calculate luminance
        luminance = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

        # Threshold commonly used is 0.5, but WCAG contrast ratios are more complex.
        # For simplicity (black/white text choice), 0.5 is a reasonable heuristic.
        return luminance > 0.5
    except Exception as e:
        print(f"Error calculating WCAG luminance for color '{color}': {e}")
        return True  # Default to assuming light background in case of error


def determine_text_color_for_dropdown(bg_color: str) -> str:
    """
    Determine appropriate text color (black or white) for a given background color.

    Uses apply_wcag_ui_standards to check background luminance.

    Args:
        bg_color (str): Background color in hex (#RRGGBB) format.

    Returns:
        str: '#000000' (black) if background is light, '#FFFFFF' (white) if background is dark.
    """
    return "#000000" if apply_wcag_ui_standards(bg_color) else "#FFFFFF"


def rgb_to_hex(rgb_color: str) -> str:
    """
    Converts an RGB color string (e.g., 'rgb(102, 197, 204)') to a hex color string (e.g., '#66C5CC').

    Args:
        rgb_color (str): The RGB color string.

    Returns:
        str: The hex color string.
    """
    try:
        # Extract the RGB values from the string
        rgb_values = rgb_color.strip("rgb()").split(",")
        r, g, b = [int(value.strip()) for value in rgb_values]
        return f"#{r:02X}{g:02X}{b:02X}"
    except Exception as e:
        # Return a default color if conversion fails
        print(f"Error converting color {rgb_color}: {e}")
        return "#000000"  # Black as fallback


class ColorManager:
    """Manages color assignment and generation for tickers."""

    def __init__(self):
        self.ticker_colors: dict[str, str] = {}
        # Track used colors to avoid duplicates
        self.used_colors: list[str] = []

    def generate_colors_for_tickers(self, tickers: list[str]) -> dict[str, str]:
        """Generate consistent colors for a list of tickers."""
        if not tickers:
            return {}

        unique_tickers = sorted(tickers)
        color_palette = px.colors.qualitative.Pastel

        self.ticker_colors = {
            ticker: color_palette[i % len(color_palette)]
            for i, ticker in enumerate(unique_tickers)
        }

        # Reset used colors when tickers change
        self.used_colors = []

        return self.ticker_colors

    def get_random_base_color(self) -> str:
        """Get a random color from base colors without repetition."""
        if not BASE_COLORS:
            return "#636EFA"

        # If all colors have been used, reset the list
        if len(self.used_colors) >= len(BASE_COLORS):
            self.used_colors = []

        # Get available colors
        available_colors = [
            c for c in BASE_COLORS if c not in self.used_colors]

        # Pick a random color from available ones
        color = random.choice(available_colors)
        self.used_colors.append(color)

        return color

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
            <h3 style="position: relative;">
                {ticker}
            </h3>
            <p class="tile-value" style="position: relative;">
                {formatted_shares}<span class="tile-label"> shares</span>
            </p>
        </div>
        """
