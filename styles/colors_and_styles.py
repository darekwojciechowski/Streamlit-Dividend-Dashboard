"""Color and style definitions module with palettes, CSS styles, and accessibility utility functions."""

# Define a list of base colors for the application
BASE_COLORS = [
    '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
    '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'
] * 2  # Repeating the list to ensure enough unique colors if needed

# Define CSS styles for the application
CSS_STYLES = """
<style>
    /* Modern Typography System 2025 - CSS Variables */
    :root {
        /* Fluid Typography using clamp() for responsive sizing */
        --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
        --text-sm: clamp(0.875rem, 0.8rem + 0.375vw, 1rem);
        --text-base: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
        --text-lg: clamp(1.125rem, 1rem + 0.625vw, 1.5rem);
        --text-xl: clamp(1.5rem, 1.3rem + 1vw, 2rem);
        --text-2xl: clamp(2rem, 1.7rem + 1.5vw, 2.5rem);
        --text-3xl: clamp(2.5rem, 2rem + 2.5vw, 3.5rem);
        
        /* Line Heights - WCAG compliant */
        --leading-tight: 1.25;
        --leading-normal: 1.5;
        --leading-relaxed: 1.75;
        --leading-loose: 2;
        
        /* Font Weights */
        --font-normal: 400;
        --font-medium: 500;
        --font-semibold: 600;
        --font-bold: 700;
        --font-extrabold: 800;
        
        /* Variable Font with fallback stack */
        --font-family: 'Inter var', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    }
    
    /* Support for variable fonts */
    @supports (font-variation-settings: normal) {
        :root {
            --font-family: 'Inter var', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
    }
    
    /* Base typography */
    body {
        font-family: var(--font-family);
        font-size: var(--text-base);
        line-height: var(--leading-normal);
        font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
    }
    
    .gradient-tile {
        transition: all 0.3s ease !important;
        color: #ffffff;
        font-family: var(--font-family);
    }
    
    .gradient-tile:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.2) !important;
    }
    
    .gradient-tile h3 {
        font-size: var(--text-lg);
        line-height: var(--leading-tight);
        font-weight: var(--font-semibold);
        margin: 0;
    }
    
    .gradient-tile .tile-value {
        font-size: var(--text-2xl);
        line-height: var(--leading-tight);
        font-weight: var(--font-extrabold);
        margin: 0.5rem 0;
    }
    
    .gradient-tile .tile-label {
        font-size: var(--text-sm);
        line-height: var(--leading-normal);
        font-weight: var(--font-medium);
    }
    
    .tiles-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        padding: 1rem;
    }
    
    /* Accessibility: Respect user's motion preferences */
    @media (prefers-reduced-motion: reduce) {
        .gradient-tile {
            transition: none !important;
        }
        .gradient-tile:hover {
            transform: none !important;
        }
    }
    
    /* Ensure minimum touch target size (44x44px WCAG AAA) */
    .gradient-tile {
        min-height: 120px;
    }
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
