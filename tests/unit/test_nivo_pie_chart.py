"""Unit tests for the NivoPieChart Nivo.js donut chart component."""

import sys
from unittest.mock import MagicMock, patch

# Patch streamlit_elements before the component module is first imported.
# The package requires a live Streamlit runtime which is unavailable during unit tests.
sys.modules["streamlit_elements"] = MagicMock()

import pytest

from app.components.nivo_pie_chart import NivoPieChart

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

VALID_PATTERN_IDS: frozenset[str] = frozenset({"dots", "lines", "horizontalLines", "squares"})

COLOR_FALLBACK: str = "#636EFA"
COLOR_RGB_TEAL: str = "rgb(102, 197, 204)"
COLOR_HEX_TEAL: str = "#66C5CC"
COLOR_HEX_RED: str = "#FF0000"
COLOR_HEX_BLUE: str = "#0000FF"

SINGLE_ITEM_DATA: list[dict] = [
    {"id": "AAPL.US", "label": "AAPL", "value": 100},
]

MULTI_ITEM_DATA: list[dict] = [
    {"id": "AAPL.US", "label": "AAPL", "value": 100},
    {"id": "MSFT.US", "label": "MSFT", "value": 200},
    {"id": "PKO.PL", "label": "PKO", "value": 50},
]

MULTI_ITEM_DATA_WITH_RGB_COLORS: list[dict] = [
    {"id": "AAPL.US", "label": "AAPL", "value": 100, "color": COLOR_RGB_TEAL},
    {"id": "MSFT.US", "label": "MSFT", "value": 200, "color": "rgb(255, 0, 0)"},
    {"id": "PKO.PL", "label": "PKO", "value": 50, "color": "rgb(0, 0, 255)"},
]

TICKER_COLORS: dict[str, str] = {
    "AAPL.US": COLOR_HEX_RED,
    "MSFT.US": COLOR_HEX_BLUE,
    "PKO.PL": COLOR_HEX_TEAL,
}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def chart_with_colors() -> NivoPieChart:
    """Chart initialised with an explicit ticker→color mapping."""
    return NivoPieChart(data=MULTI_ITEM_DATA, colors=TICKER_COLORS)


@pytest.fixture
def chart_without_colors_rgb() -> NivoPieChart:
    """Chart initialised without a colors dict; items carry raw rgb() strings."""
    return NivoPieChart(data=MULTI_ITEM_DATA_WITH_RGB_COLORS)


@pytest.fixture
def chart_default() -> NivoPieChart:
    """Chart initialised without a colors dict and no 'color' key in items."""
    return NivoPieChart(data=MULTI_ITEM_DATA)


# ===========================================================================
# Test classes
# ===========================================================================


@pytest.mark.unit
class TestNivoPieChartInitialization:
    """Verify object construction stores parameters correctly."""

    def test_default_height_is_500(self) -> None:
        chart = NivoPieChart(data=MULTI_ITEM_DATA)
        assert chart.height == 500

    def test_custom_height_is_stored(self) -> None:
        chart = NivoPieChart(data=MULTI_ITEM_DATA, height=800)
        assert chart.height == 800

    def test_data_length_preserved_with_colors(self, chart_with_colors: NivoPieChart) -> None:
        assert len(chart_with_colors.data) == len(MULTI_ITEM_DATA)

    def test_data_length_preserved_without_colors(self, chart_without_colors_rgb: NivoPieChart) -> None:
        assert len(chart_without_colors_rgb.data) == len(MULTI_ITEM_DATA_WITH_RGB_COLORS)

    def test_data_ids_preserved_with_colors(self, chart_with_colors: NivoPieChart) -> None:
        original_ids = {item["id"] for item in MULTI_ITEM_DATA}
        result_ids = {item["id"] for item in chart_with_colors.data}
        assert result_ids == original_ids

    def test_data_ids_preserved_without_colors(self, chart_without_colors_rgb: NivoPieChart) -> None:
        original_ids = {item["id"] for item in MULTI_ITEM_DATA_WITH_RGB_COLORS}
        result_ids = {item["id"] for item in chart_without_colors_rgb.data}
        assert result_ids == original_ids

    def test_original_data_not_mutated(self) -> None:
        original = [{"id": "AAPL.US", "label": "AAPL", "value": 100}]
        original_copy = [dict(item) for item in original]
        NivoPieChart(data=original, colors={"AAPL.US": COLOR_HEX_RED})
        assert original == original_copy


@pytest.mark.unit
class TestNivoPieChartColorProcessing:
    """Verify colour assignment from dict or item-level color keys."""

    def test_color_applied_from_dict(self, chart_with_colors: NivoPieChart) -> None:
        for item in chart_with_colors.data:
            assert item["color"] == TICKER_COLORS[item["id"]]

    def test_missing_ticker_in_dict_uses_fallback(self) -> None:
        chart = NivoPieChart(data=MULTI_ITEM_DATA, colors={})
        for item in chart.data:
            assert item["color"] == COLOR_FALLBACK

    def test_partial_colors_dict_uses_fallback_for_missing(self) -> None:
        partial_colors = {"AAPL.US": COLOR_HEX_RED}
        chart = NivoPieChart(data=MULTI_ITEM_DATA, colors=partial_colors)
        aapl = next(i for i in chart.data if i["id"] == "AAPL.US")
        msft = next(i for i in chart.data if i["id"] == "MSFT.US")
        assert aapl["color"] == COLOR_HEX_RED
        assert msft["color"] == COLOR_FALLBACK

    @pytest.mark.parametrize(
        ("input_color", "expected_hex"),
        [
            pytest.param(COLOR_RGB_TEAL, COLOR_HEX_TEAL, id="rgb-teal"),
            pytest.param("rgb(255, 0, 0)", "#FF0000", id="rgb-red"),
            pytest.param("rgb(0, 0, 255)", "#0000FF", id="rgb-blue"),
            pytest.param("rgb(0, 255, 0)", "#00FF00", id="rgb-green"),
        ],
    )
    def test_rgb_color_converted_to_hex(self, input_color: str, expected_hex: str) -> None:
        data = [{"id": "X.US", "label": "X", "value": 1, "color": input_color}]
        chart = NivoPieChart(data=data)
        assert chart.data[0]["color"] == expected_hex

    def test_hex_color_passed_through_unchanged(self) -> None:
        data = [{"id": "X.US", "label": "X", "value": 1, "color": COLOR_HEX_RED}]
        chart = NivoPieChart(data=data)
        assert chart.data[0]["color"] == COLOR_HEX_RED

    def test_missing_color_key_uses_fallback(self, chart_default: NivoPieChart) -> None:
        for item in chart_default.data:
            assert item["color"] == COLOR_FALLBACK

    def test_rgb_colors_in_data_all_converted(self, chart_without_colors_rgb: NivoPieChart) -> None:
        for item in chart_without_colors_rgb.data:
            assert item["color"].startswith("#"), f"Expected hex color, got: {item['color']!r}"


@pytest.mark.unit
class TestNivoPieChartPatterns:
    """Verify that defs, fill and per-item patterns are correctly formed."""

    def test_each_item_has_pattern_key(self, chart_with_colors: NivoPieChart) -> None:
        for item in chart_with_colors.data:
            assert "pattern" in item

    def test_each_pattern_is_valid_id(self, chart_with_colors: NivoPieChart) -> None:
        for item in chart_with_colors.data:
            assert item["pattern"] in VALID_PATTERN_IDS, f"Unexpected pattern id: {item['pattern']!r}"

    def test_fill_length_matches_data(self, chart_with_colors: NivoPieChart) -> None:
        assert len(chart_with_colors.config["fill"]) == len(MULTI_ITEM_DATA)

    def test_fill_ids_match_data_ids(self, chart_with_colors: NivoPieChart) -> None:
        fill_ids = {entry["match"]["id"] for entry in chart_with_colors.config["fill"]}
        data_ids = {item["id"] for item in chart_with_colors.data}
        assert fill_ids == data_ids

    def test_fill_pattern_ids_are_valid(self, chart_with_colors: NivoPieChart) -> None:
        for entry in chart_with_colors.config["fill"]:
            assert entry["id"] in VALID_PATTERN_IDS

    def test_defs_contains_all_four_pattern_types(self, chart_with_colors: NivoPieChart) -> None:
        def_ids = {d["id"] for d in chart_with_colors.config["defs"]}
        assert def_ids == VALID_PATTERN_IDS

    def test_fill_references_only_defined_patterns(self, chart_with_colors: NivoPieChart) -> None:
        defined_ids = {d["id"] for d in chart_with_colors.config["defs"]}
        for entry in chart_with_colors.config["fill"]:
            assert entry["id"] in defined_ids

    def test_fill_pattern_id_matches_item_pattern_key(self, chart_with_colors: NivoPieChart) -> None:
        fill_by_id = {entry["match"]["id"]: entry["id"] for entry in chart_with_colors.config["fill"]}
        for item in chart_with_colors.data:
            assert fill_by_id[item["id"]] == item["pattern"]


@pytest.mark.unit
class TestNivoPieChartConfig:
    """Verify Nivo.js configuration values match design requirements."""

    def test_inner_radius_is_0_5(self, chart_with_colors: NivoPieChart) -> None:
        assert chart_with_colors.config["innerRadius"] == 0.5

    def test_arc_labels_skip_angle_is_360(self, chart_with_colors: NivoPieChart) -> None:
        assert chart_with_colors.config["arcLabelsSkipAngle"] == 360

    def test_legends_is_empty_list(self, chart_with_colors: NivoPieChart) -> None:
        assert chart_with_colors.config["legends"] == []

    def test_margin_has_all_four_sides(self, chart_with_colors: NivoPieChart) -> None:
        margin = chart_with_colors.config["margin"]
        assert {"top", "right", "bottom", "left"} <= set(margin.keys())

    def test_margin_values_are_positive(self, chart_with_colors: NivoPieChart) -> None:
        for side, value in chart_with_colors.config["margin"].items():
            assert value > 0, f"Margin '{side}' should be positive, got {value}"

    def test_tooltip_container_has_required_keys(self, chart_with_colors: NivoPieChart) -> None:
        container = chart_with_colors.config["theme"]["tooltip"]["container"]
        assert "background" in container
        assert "color" in container
        assert "borderRadius" in container

    def test_border_color_defined_from_datum(self, chart_with_colors: NivoPieChart) -> None:
        assert chart_with_colors.config["borderColor"].get("from") == "color"

    def test_pad_angle_positive(self, chart_with_colors: NivoPieChart) -> None:
        assert chart_with_colors.config["padAngle"] > 0

    def test_corner_radius_non_negative(self, chart_with_colors: NivoPieChart) -> None:
        assert chart_with_colors.config["cornerRadius"] >= 0

    def test_active_outer_radius_offset_positive(self, chart_with_colors: NivoPieChart) -> None:
        assert chart_with_colors.config["activeOuterRadiusOffset"] > 0

    def test_arc_link_labels_color_from_datum(self, chart_with_colors: NivoPieChart) -> None:
        assert chart_with_colors.config["arcLinkLabelsColor"].get("from") == "color"

    def test_arc_link_labels_skip_angle_non_negative(self, chart_with_colors: NivoPieChart) -> None:
        assert chart_with_colors.config["arcLinkLabelsSkipAngle"] >= 0

    def test_border_width_non_negative(self, chart_with_colors: NivoPieChart) -> None:
        assert chart_with_colors.config["borderWidth"] >= 0


@pytest.mark.unit
class TestNivoPieChartEdgeCases:
    """Verify graceful behaviour at boundary conditions."""

    def test_empty_data_produces_empty_data_list(self) -> None:
        chart = NivoPieChart(data=[], colors={})
        assert chart.data == []

    def test_empty_data_fill_is_empty(self) -> None:
        chart = NivoPieChart(data=[], colors={})
        assert chart.config["fill"] == []

    def test_single_item_with_colors(self) -> None:
        chart = NivoPieChart(data=SINGLE_ITEM_DATA, colors={"AAPL.US": COLOR_HEX_RED})
        assert len(chart.data) == 1
        assert chart.data[0]["color"] == COLOR_HEX_RED

    def test_single_item_pattern_is_valid(self) -> None:
        chart = NivoPieChart(data=SINGLE_ITEM_DATA, colors={"AAPL.US": COLOR_HEX_RED})
        assert chart.data[0]["pattern"] in VALID_PATTERN_IDS

    def test_zero_value_item_accepted(self) -> None:
        data = [{"id": "AAPL.US", "label": "AAPL", "value": 0}]
        chart = NivoPieChart(data=data, colors={"AAPL.US": COLOR_HEX_RED})
        assert chart.data[0]["value"] == 0

    def test_large_dataset_preserves_all_items(self) -> None:
        data = [{"id": f"TICKER{i}.US", "label": f"T{i}", "value": i + 1} for i in range(50)]
        colors = {f"TICKER{i}.US": COLOR_HEX_RED for i in range(50)}
        chart = NivoPieChart(data=data, colors=colors)
        assert len(chart.data) == 50

    def test_extra_item_keys_preserved(self) -> None:
        data = [{"id": "AAPL.US", "label": "AAPL", "value": 100, "extra": "custom_value"}]
        chart = NivoPieChart(data=data, colors={"AAPL.US": COLOR_HEX_RED})
        assert chart.data[0]["extra"] == "custom_value"


@pytest.mark.unit
class TestNivoPieChartRender:
    """Verify render() calls the Nivo.js runtime with correct arguments."""

    def test_render_calls_nivo_pie_once(self, chart_with_colors: NivoPieChart) -> None:
        with (
            patch("app.components.nivo_pie_chart.elements"),
            patch("app.components.nivo_pie_chart.mui"),
            patch("app.components.nivo_pie_chart.nivo") as mock_nivo,
        ):
            chart_with_colors.render()

        mock_nivo.Pie.assert_called_once()

    def test_render_passes_correct_data(self, chart_with_colors: NivoPieChart) -> None:
        with (
            patch("app.components.nivo_pie_chart.elements"),
            patch("app.components.nivo_pie_chart.mui"),
            patch("app.components.nivo_pie_chart.nivo") as mock_nivo,
        ):
            chart_with_colors.render()

        _, kwargs = mock_nivo.Pie.call_args
        assert kwargs["data"] == chart_with_colors.data

    def test_render_passes_datum_color_scheme(self, chart_with_colors: NivoPieChart) -> None:
        with (
            patch("app.components.nivo_pie_chart.elements"),
            patch("app.components.nivo_pie_chart.mui"),
            patch("app.components.nivo_pie_chart.nivo") as mock_nivo,
        ):
            chart_with_colors.render()

        _, kwargs = mock_nivo.Pie.call_args
        assert kwargs["colors"] == {"datum": "data.color"}

    def test_render_opens_elements_with_chart_key(self, chart_with_colors: NivoPieChart) -> None:
        with (
            patch("app.components.nivo_pie_chart.elements") as mock_elements,
            patch("app.components.nivo_pie_chart.mui"),
            patch("app.components.nivo_pie_chart.nivo"),
        ):
            chart_with_colors.render()

        mock_elements.assert_called_once_with("nivo_pie_chart")

    def test_render_creates_mui_box(self, chart_with_colors: NivoPieChart) -> None:
        with (
            patch("app.components.nivo_pie_chart.elements"),
            patch("app.components.nivo_pie_chart.mui") as mock_mui,
            patch("app.components.nivo_pie_chart.nivo"),
        ):
            chart_with_colors.render()

        mock_mui.Box.assert_called_once()

    def test_render_mui_box_sx_contains_height(self, chart_with_colors: NivoPieChart) -> None:
        with (
            patch("app.components.nivo_pie_chart.elements"),
            patch("app.components.nivo_pie_chart.mui") as mock_mui,
            patch("app.components.nivo_pie_chart.nivo"),
        ):
            chart_with_colors.render()

        _, kwargs = mock_mui.Box.call_args
        assert "height" in kwargs.get("sx", {})

    def test_render_passes_config_to_nivo_pie(self, chart_with_colors: NivoPieChart) -> None:
        with (
            patch("app.components.nivo_pie_chart.elements"),
            patch("app.components.nivo_pie_chart.mui"),
            patch("app.components.nivo_pie_chart.nivo") as mock_nivo,
        ):
            chart_with_colors.render()

        _, kwargs = mock_nivo.Pie.call_args
        assert kwargs["innerRadius"] == 0.5
        assert kwargs["legends"] == []
