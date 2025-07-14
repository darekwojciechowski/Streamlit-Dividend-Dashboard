"""
Configuration settings for the Dividend Dashboard application.
Contains all configurable constants and default values.
"""

# Default values for dividend calculator
DEFAULT_GROWTH_PERCENTAGE = 4.0
DEFAULT_NUM_YEARS = 15

# UI Configuration
DEFAULT_PAGE_TITLE = "Dividend Dashboard"
DEFAULT_SIDEBAR_STATE = "expanded"
DEFAULT_DASHBOARD_TITLE = "Dividend Data Visualization Dashboard"

# Data Configuration
DATA_FILE_PATH = "data/dividend_data.csv"

# Color Theme Configuration (Purple/Violet theme)
COLOR_THEME = {
    "primary": "#8A2BE2",      # Main purple
    "secondary": "#A688D1",    # Light purple
    "accent": "#6B46C1",       # Deep purple
    "fallback": "#1f77b4",     # Default fallback blue
    "success": "#10B981",      # Green for success
    "warning": "#F59E0B"     # Amber for warnings

}

# Chart Configuration
CHART_CONFIG = {
    "bar_chart": {
        "title": "Total Net Dividends by Ticker",
        "x_title": "Ticker",
        "y_title": "Total Net Dividend (USD)",
        "hover_mode": "x unified"
    },
    "pie_chart": {
        "title": "Dividend Distribution",
        "title_font_size": "17px"
    },
    "projection_chart": {
        "trend_line_color": COLOR_THEME["primary"],
        "trend_line_width": 2,
        "trend_line_dash": "dot",
        "marker_size": 5,
        "fallback_color": COLOR_THEME["fallback"]
    }
}

# Slider Configuration
SLIDER_CONFIG = {
    "min_years": 1,
    "max_years": 30,
    "step": 1
}

# Number Input Configuration
GROWTH_INPUT_CONFIG = {
    "min_value": 0.0,
    "step": 0.1,
    "format": "%.1f"
}

# Messages Configuration
MESSAGES = {
    "no_ticker_data": "No ticker data available to select.",
    "no_share_data": "No share data to display metrics for the selected tickers.",
    "no_dividend_data": "No valid 'Net Dividend' data available for the selected tickers to display charts.",
    "no_data_charts": "No data to display charts for the selected tickers.",
    "select_tickers_calculator": "Please select tickers with data to use the calculator.",
    "no_tickers_calculation": "No tickers available for calculation.",
    "select_ticker_projection": "Select a ticker to see the projection.",
    "calculator_description": "Project future dividend income based on selected annual growth rate and investment period."
}

# Form Labels Configuration
LABELS = {
    "ticker_select": "Select tickers to analyze:",
    "company_projection": "Select a company for projection:",
    "growth_percentage": "Annual dividend growth (%)",
    "projection_years": "Projection years",
    "total_shares_header": "## Total Shares per Ticker",
    "charts_header": "## Dividend Analysis Charts",
    "calculator_header": "Dividend Growth Calculator"
}
