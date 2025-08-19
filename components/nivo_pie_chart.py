
import streamlit as st
from streamlit_elements import elements, mui
from streamlit_elements import nivo
import random
from styles.colors_and_styles import rgb_to_hex


class NivoPieChart:
    """Simplified Nivo pie chart component."""

    def __init__(self, data, colors=None, height=500):
        """Initialize pie chart with essential parameters only."""
        # Process data with colors
        if colors:
            self.data = [
                {**item,
                    "color": rgb_to_hex(colors.get(item["id"], "#636EFA"))}
                for item in data
            ]
        else:
            self.data = [
                {**item, "color": rgb_to_hex(item.get("color", "#636EFA"))}
                for item in data
            ]

        self.height = height

        # Simplified configuration
        self.config = {
            "margin": {"top": 30, "right": 110, "bottom": 30, "left": 110},
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
            "theme": {
                "tooltip": {
                    "container": {
                        "background": "rgba(30, 41, 59, 0.95)",
                        "color": "#f1f5f9",
                        "fontSize": 18,
                        "fontFamily": "Inter, Segoe UI, Arial, sans-serif",
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
