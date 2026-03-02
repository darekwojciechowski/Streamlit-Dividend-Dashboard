"""
Configuration settings for the Dividend Dashboard application.
Contains all configurable constants and default values.
"""

# Default values for dividend calculator
DEFAULT_GROWTH_PERCENTAGE = 7.0
DEFAULT_NUM_YEARS = 15

# UI Configuration
DEFAULT_PAGE_TITLE = "Dividend Dashboard"
DEFAULT_SIDEBAR_STATE = "expanded"
DEFAULT_LAYOUT = "centered"
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
