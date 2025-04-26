"""
Color and Style Definitions for Dividend Dashboard

This module centralizes color palettes, CSS styles, and utility functions
related to visual styling and accessibility for the Streamlit application.

Constants:
- BASE_COLORS: A list of hex color codes for general use (e.g., charts, tiles).
- CSS_STYLES: A string containing CSS rules for custom styling of components
              (e.g., gradient tiles).

Functions:
- adjust_gradient: Modifies a color to create a gradient effect.
- apply_wcag_ui_standards: Determines if a color is light or dark based on luminance.
- determine_text_color_for_dropdown: Suggests black or white text based on a
                                     background color for contrast.
"""

# colors_and_styles.py

'''
Theme Configuration Note:

The primary color (#8A2BE2 - Violet) and base theme (dark) are primarily
configured via the .streamlit/config.toml file for Streamlit's built-in widgets.

Example .streamlit/config.toml:
[theme]
base="dark"
primaryColor="#8a2be2"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor="#fffafa"

This file defines constants and functions for custom components or elements
not directly styled by the Streamlit theme (e.g., Plotly charts, custom HTML).
'''

# Define a list of base colors for the application
BASE_COLORS = [
    '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
    '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'
] * 2  # Repeating the list to ensure enough unique colors if needed

# Define CSS styles for the application
CSS_STYLES = """
<style>
    .gradient-tile {
        transition: all 0.3s ease !important;
        /* Default text color set here, but can be overridden by inline style */
        color: #ffffff;
    }
    .gradient-tile:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.2) !important;
    }
    .tiles-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        padding: 1rem;
    }
    /* Add other global custom styles here if needed */
</style>
"""


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
