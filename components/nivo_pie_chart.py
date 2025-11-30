
import streamlit as st
from streamlit_elements import elements, mui
from streamlit_elements import nivo
import random
from styles.colors_and_styles import rgb_to_hex


class NivoPieChart:
    """Simplified Nivo pie chart component."""

    def __init__(self, data, colors=None, height=500):
        """Initialize pie chart with essential parameters only."""
        # Define available patterns
        self.patterns = [
            {"id": "dots", "type": "patternDots", "background": "inherit",
                "color": "rgba(255, 255, 255, 0.3)", "size": 4, "padding": 1, "stagger": True},
            {"id": "lines", "type": "patternLines", "background": "inherit",
                "color": "rgba(255, 255, 255, 0.3)", "rotation": -45, "lineWidth": 6, "spacing": 10},
            {"id": "horizontalLines", "type": "patternLines", "background": "inherit",
                "color": "rgba(255, 255, 255, 0.3)", "rotation": 0, "lineWidth": 6, "spacing": 10},
            {"id": "squares", "type": "patternSquares", "background": "inherit",
                "color": "rgba(255, 255, 255, 0.3)", "size": 6, "padding": 2, "stagger": True}
        ]

        # Process data with colors and random patterns
        if colors:
            self.data = [
                {**item,
                    "color": rgb_to_hex(colors.get(item["id"], "#636EFA")),
                    "pattern": random.choice(self.patterns)["id"]}
                for item in data
            ]
        else:
            self.data = [
                {**item,
                 "color": rgb_to_hex(item.get("color", "#636EFA")),
                 "pattern": random.choice(self.patterns)["id"]}
                for item in data
            ]

        self.height = height

        # Simplified configuration
        self.config = {
            "margin": {"top": 80, "right": 110, "bottom": 80, "left": 110},
            "innerRadius": 0.5,
            "padAngle": 0.7,
            "cornerRadius": 3,
            "activeOuterRadiusOffset": 6,
            "borderWidth": 1,
            "borderColor": {"from": "color", "modifiers": [["darker", 0.8]]},
            "arcLinkLabelsSkipAngle": 10,
            "arcLinkLabelsTextColor": "grey",
            "arcLinkLabelsThickness": 2,
            "arcLinkLabelsColor": {"from": "color"},
            "arcLabelsSkipAngle": 360,  # Skip all arc labels
            "legends": [],
            "defs": self.patterns,
            "fill": [
                {"match": {"id": item["id"]}, "id": item["pattern"]}
                for item in self.data
            ],
            "theme": {
                "tooltip": {
                    "container": {
                        "background": "rgba(30, 41, 59, 0.95)",
                        "color": "#f1f5f9",
                        "fontSize": "clamp(1rem, 0.95rem + 0.25vw, 1.125rem)",
                        "fontFamily": "'Inter var', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif",
                        "lineHeight": "1.5",
                        "fontWeight": "500",
                        "padding": "16px 24px",
                        "borderRadius": "16px",
                        "boxShadow": "0 8px 32px 0 rgba(31, 38, 135, 0.37)",
                        "backdropFilter": "blur(6px)",
                        "border": "none",
                    }
                }
            }
        }

    def render(self):
        """Render the pie chart."""
        with elements("nivo_pie_chart"):
            with mui.Box(sx={
                "height": self.height,
                "width": "100%",
                "minHeight": "300px",
                "maxWidth": "100%"
            }):
                nivo.Pie(
                    data=self.data,
                    colors={"datum": "data.color"},
                    **self.config
                )
