
import streamlit as st
from streamlit_elements import elements, mui
from streamlit_elements import nivo
import random


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


class NivoPieChart:
    def __init__(
        self,
        data,
        colors=None,  # Should always be provided for consistency!
        height=500,
        margin=None,
        inner_radius=0.5,
        pad_angle=0.7,
        corner_radius=3,
        active_outer_radius_offset=8,
        border_width=1,
        border_color=None,
        arc_link_labels_skip_angle=10,
        arc_link_labels_text_color="grey",
        arc_link_labels_thickness=2,
        arc_link_labels_color=None,
        arc_labels_skip_angle=10,
        arc_labels_text_color=None,
        defs=None,
        fill=None,
        theme=None,
        legends=None,
        key="nivo_pie_chart"
    ):
        # Always assign colors deterministically if provided
        if colors is not None:
            self.data = [
                {
                    **item,
                    "color": rgb_to_hex(colors.get(item["id"], item.get("color", "#636EFA")))
                }
                for item in data
            ]
        else:
            # Log a warning if colors are not provided
            print("Warning: No colors provided. Using default color for all segments.")
            self.data = [
                {
                    **item,
                    # Default color
                    "color": rgb_to_hex(item.get("color", "#636EFA"))
                }
                for item in data
            ]

        # Debugging: Print the processed data with colors
        # print("Processed Data with Colors:", self.data)

        self.height = height
        self.margin = margin or {"top": 100,
                                 "right": 100, "bottom": 100, "left": 100}
        self.inner_radius = inner_radius
        self.pad_angle = pad_angle
        self.corner_radius = corner_radius
        self.active_outer_radius_offset = active_outer_radius_offset
        self.border_width = border_width
        self.border_color = border_color or {
            "from": "color", "modifiers": [["darker", 0.8]]}
        self.arc_link_labels_skip_angle = arc_link_labels_skip_angle
        self.arc_link_labels_text_color = arc_link_labels_text_color
        self.arc_link_labels_thickness = arc_link_labels_thickness
        self.arc_link_labels_color = arc_link_labels_color or {"from": "color"}
        self.arc_labels_skip_angle = arc_labels_skip_angle
        self.arc_labels_text_color = arc_labels_text_color or {
            "from": "color", "modifiers": [["darker", 4]]}
        self.defs = defs or [
            {
                "id": "dots",
                "type": "patternDots",
                "background": "inherit",
                "color": "rgba(255, 255, 255, 0.3)",
                "size": 4,
                "padding": 1,
                "stagger": True,
            },
            {
                "id": "lines",
                "type": "patternLines",
                "background": "inherit",
                "color": "rgba(255, 255, 255, 0.3)",
                "rotation": -45,
                "lineWidth": 6,
                "spacing": 10,
            },
            {
                "id": "circles",
                "type": "patternCircles",
                "background": "inherit",
                "color": "rgba(255,255,255,0.25)",
                "size": 6,
                "padding": 2,
                "stagger": False,
            },
        ]
        patterns = ["dots", "lines", "circles"]
        if not fill:
            self.fill = [
                {"match": {"id": item["id"]}, "id": random.choice(patterns)}
                for item in self.data
            ]
            # Debugging: Print the generated fill configuration
            print("Generated Fill Configuration:", self.fill)
        else:
            self.fill = fill
        self.theme = theme or {
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
                    "transition": "all 0.2s cubic-bezier(.4,0,.2,1)",
                    "minWidth": "120px",
                    "maxWidth": "260px",
                    "display": "flex",
                    "flexDirection": "column",
                    "alignItems": "flex-start",
                    "gap": "6px",
                },
                "basic": {
                    "whiteSpace": "pre",
                    "display": "flex",
                    "flexDirection": "column",
                    "alignItems": "flex-start",
                    "justifyContent": "center",
                    "background": "none",
                    "margin": 0,
                    "padding": 0,
                    "width": "auto",
                    "height": "auto",
                    "color": "inherit",
                },
            },
            "legends": {
                "text": {
                    "fontSize": "13",
                }
            },
        }
        self.legends = legends or [
            {
                "anchor": "bottom",
                "direction": "row",
                "justify": False,
                "translateX": 0,
                "translateY": 90,
                "itemsSpacing": 0,
                "itemWidth": 100,
                "itemHeight": 18,
                "itemTextColor": "#999",
                "itemDirection": "left-to-right",
                "itemOpacity": 1,
                "symbolSize": 20,
                "symbolShape": "circle",
                "effects": [
                    {"on": "hover", "style": {"itemTextColor": "#fafafa"}}
                ],
            }
        ]
        self.key = key

    def render(self):
        with elements(self.key):
            with mui.Box(sx={"height": self.height}):
                nivo.Pie(
                    data=self.data,
                    margin=self.margin,
                    innerRadius=self.inner_radius,
                    padAngle=self.pad_angle,
                    cornerRadius=self.corner_radius,
                    activeOuterRadiusOffset=self.active_outer_radius_offset,
                    borderWidth=self.border_width,
                    borderColor=self.border_color,
                    arcLinkLabelsSkipAngle=self.arc_link_labels_skip_angle,
                    arcLinkLabelsTextColor=self.arc_link_labels_text_color,
                    arcLinkLabelsThickness=self.arc_link_labels_thickness,
                    arcLinkLabelsColor=self.arc_link_labels_color,
                    arcLabelsSkipAngle=360,  # Skip all arc labels
                    arcLabelsTextColor=None,  # Disable arc labels text color
                    defs=self.defs,
                    fill=self.fill,
                    theme=self.theme,
                    legends=self.legends,
                    # Use the color field from the data
                    colors={"datum": "data.color"},
                )


# Example usage:
if __name__ == "__main__":
    DATA_PIE = [
        {"id": "css", "label": "css", "value": 58},
        {"id": "php", "label": "php", "value": 582},
        {"id": "ruby", "label": "ruby", "value": 491},
        {"id": "scala", "label": "scala", "value": 254},
        {"id": "stylus", "label": "stylus", "value": 598}
    ]
    COLORS = {
        "css": "hsl(309, 70%, 50%)",
        "php": "hsl(229, 70%, 50%)",
        "ruby": "hsl(78, 70%, 50%)",
        "scala": "hsl(278, 70%, 50%)",
        "stylus": "hsl(273, 70%, 50%)"
    }
    chart = NivoPieChart(DATA_PIE, colors=COLORS)
    chart.render()
