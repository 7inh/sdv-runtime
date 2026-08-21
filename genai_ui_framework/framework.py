from enum import Enum
from itertools import count
from pathlib import Path

from nicegui import app, ui


_ASSET_URL_PREFIX = "/etas"
_ASSET_DIR = Path(__file__).resolve().parent / "static"

app.add_static_files(_ASSET_URL_PREFIX, str(_ASSET_DIR))


def _asset_path(path: str) -> str:
    return f"{_ASSET_URL_PREFIX}/{path.lstrip('/')}"


class GaugeType(str, Enum):
    GENERIC = "GENERIC"
    SPEED = "SPEED"
    TORQUE = "TORQUE"
    FUEL = "FUEL"


class GaugeStyle(str, Enum):
    MODERN = "MODERN"
    RETRO = "RETRO"
    DEFAULT = "DEFAULT"


class ControlLightIcon(str, Enum):
    NONE = "NONE"

    # Lighting / direction indicators
    HEADLIGHTS = "HEADLIGHTS"
    DIPPED_BEAM = "DIPPED_BEAM"
    FOG_LIGHT = "FOG_LIGHT"
    ARROW_LEFT = "ARROW_LEFT"
    ARROW_RIGHT = "ARROW_RIGHT"

    # Warnings / vehicle status
    AIRBAG = "AIRBAG"
    BRAKE_WARNING = "BRAKE_WARNING"
    CAR_BATTERY = "CAR_BATTERY"
    ENGINE = "ENGINE"
    OIL_PRESSURE_LOW = "OIL_PRESSURE_LOW"
    POWER_STEERING_WARNING = "POWER_STEERING_WARNING"
    SEATBELT = "SEATBELT"
    SEATBELT_OUTLINE = "SEATBELT_OUTLINE"

    # Body / access status
    CAR_DOORS_OPEN = "CAR_DOORS_OPEN"
    CAR_HOOD_OPEN = "CAR_HOOD_OPEN"
    CAR_TRUNK_OPEN = "CAR_TRUNK_OPEN"

    # Fluids / climate / visibility
    GAS = "GAS"
    SNOWFLAKE = "SNOWFLAKE"
    WINDSCREEN = "WINDSCREEN"
    WINDSCREEN_WASHER = "WINDSCREEN_WASHER"


_CONTROL_LIGHT_ICON_PATHS = {
    # Lighting / direction indicators
    ControlLightIcon.HEADLIGHTS: _asset_path("controllights/headlights.svg"),
    ControlLightIcon.DIPPED_BEAM: _asset_path("controllights/dipped-beam.svg"),
    ControlLightIcon.FOG_LIGHT: _asset_path("controllights/fog-light.svg"),
    ControlLightIcon.ARROW_LEFT: _asset_path("controllights/arrow-fat-left-fill.svg"),
    ControlLightIcon.ARROW_RIGHT: _asset_path("controllights/arrow-fat-right-fill.svg"),

    # Warnings / vehicle status
    ControlLightIcon.AIRBAG: _asset_path("controllights/airbag.svg"),
    ControlLightIcon.BRAKE_WARNING: _asset_path("controllights/brake-warning.svg"),
    ControlLightIcon.CAR_BATTERY: _asset_path("controllights/car-battery.svg"),
    ControlLightIcon.ENGINE: _asset_path("controllights/engine.svg"),
    ControlLightIcon.OIL_PRESSURE_LOW: _asset_path("controllights/oil-pressure-low.svg"),
    ControlLightIcon.POWER_STEERING_WARNING: _asset_path("controllights/power-steering-warning.svg"),
    ControlLightIcon.SEATBELT: _asset_path("controllights/seatbelt-fill.svg"),
    ControlLightIcon.SEATBELT_OUTLINE: _asset_path("controllights/seatbelt.svg"),

    # Body / access status
    ControlLightIcon.CAR_DOORS_OPEN: _asset_path("controllights/car-doors-open.svg"),
    ControlLightIcon.CAR_HOOD_OPEN: _asset_path("controllights/car-hood-open.svg"),
    ControlLightIcon.CAR_TRUNK_OPEN: _asset_path("controllights/car-trunk-open.svg"),

    # Fluids / climate / visibility
    ControlLightIcon.GAS: _asset_path("controllights/gas-pump-fill.svg"),
    ControlLightIcon.SNOWFLAKE: _asset_path("controllights/snowflake.svg"),
    ControlLightIcon.WINDSCREEN: _asset_path("controllights/windscreen.svg"),
    ControlLightIcon.WINDSCREEN_WASHER: _asset_path("controllights/windscreen-washer.svg"),
}


_retro_slider_counter = count(1)


class CarDashboardLayout:
    def __init__(
        self,
        width: int,
        height: int | None = None,
        *,
        gap: int = 12,
        background: str | None = None,
        align_items: str = "stretch",
        justify_content: str = "flex-start",
    ) -> None:
        outer_styles = [
            "display: flex;",
            "justify-content: center;",
            "width: 100%;",
        ]

        surface_styles = [
            f"width: {width}px;",
            "display: flex;",
            "flex-direction: row;",
            "flex-wrap: nowrap;",
            f"gap: {gap}px;",
            f"align-items: {align_items};",
            f"justify-content: {justify_content};",
            "overflow: hidden;",
            "box-sizing: border-box;",
        ]

        if height is not None:
            surface_styles.append(f"height: {height}px;")

        if background is not None:
            ui.query("body").style(f"background: {background};margin: 0;")
            outer_styles.append(f"background: {background};")
            surface_styles.append(f"background: {background};")

        with ui.element("div").style("".join(outer_styles)) as outer:
            with ui.element("div").style("".join(surface_styles)) as surface:
                pass

        self.outer = outer
        self.surface = surface

    def add_slot(
        self,
        *,
        grow: int = 1,
        shrink: int = 1,
        basis: str = "0",
        min_width: str = "0",
        align_self: str = "stretch",
        justify: str = "flex-start",
        direction: str = "column",
        overflow: str = "hidden",
        padding: int | str | None = None,
    ):
        slot_styles = [
            "display: flex;",
            f"flex-direction: {direction};",
            f"flex: {grow} {shrink} {basis};",
            f"min-width: {min_width};",
            f"align-self: {align_self};",
            f"justify-content: {justify};",
            f"overflow: {overflow};",
            "box-sizing: border-box;",
        ]

        if padding is not None:
            if isinstance(padding, int):
                slot_styles.append(f"padding: {padding}px;")
            else:
                slot_styles.append(f"padding: {padding};")

        with self.surface:
            return ui.element("div").style("".join(slot_styles))


def create_gauge(
    gauge_type: GaugeType = GaugeType.GENERIC,
    style: GaugeStyle = GaugeStyle.MODERN,
    *,
    show_readout: bool = False,
    show_scale_ring: bool = False,
    min_value: int = 0,
    max_value: int = 200,
    split_number: int = 4,
    inner_background: str = "#050505",
    size: int = 320,
):
    if gauge_type == GaugeType.SPEED and style == GaugeStyle.RETRO:
        return _create_speed_gauge_retro_svg(
            show_readout=show_readout,
            show_scale_ring=show_scale_ring,
        )

    if gauge_type == GaugeType.SPEED and style == GaugeStyle.DEFAULT:
        return _create_speed_gauge_default_svg(
            show_readout=show_readout,
            show_scale_ring=show_scale_ring,
        )

    if gauge_type == GaugeType.SPEED and style == GaugeStyle.MODERN:
        return _create_speed_gauge_modern(show_readout=show_readout)

    if gauge_type == GaugeType.TORQUE and style == GaugeStyle.DEFAULT:
        return _create_torque_gauge_default_svg(
            show_readout=show_readout,
        )

    if gauge_type == GaugeType.FUEL and style == GaugeStyle.DEFAULT:
        return _create_fuel_gauge_default_svg(
            show_readout=show_readout,
        )

    if gauge_type == GaugeType.GENERIC and style == GaugeStyle.MODERN:
        return _create_generic_gauge_modern(
            min_value=min_value,
            max_value=max_value,
            split_number=split_number,
        )

    if gauge_type == GaugeType.GENERIC and style == GaugeStyle.RETRO:
        return _create_generic_gauge_retro(
            min_value=min_value,
            max_value=max_value,
            split_number=split_number,
            inner_background=inner_background,
            size=size,
        )

    if gauge_type == GaugeType.GENERIC and style == GaugeStyle.DEFAULT:
        return _create_generic_gauge_retro(
            min_value=min_value,
            max_value=max_value,
            split_number=split_number,
            inner_background=inner_background,
            size=size,
        )

    raise ValueError(f"Unsupported gauge configuration: {gauge_type=} {style=}")


def _scale(value: float, factor: float, minimum: int = 1) -> int:
    return max(minimum, int(round(value * factor)))


def create_slider(
    style: GaugeStyle = GaugeStyle.MODERN,
    *,
    min: int = 0,
    max: int = 100,
    step: int = 1,
    value: int = 0,
    on_change=None,
):
    if style == GaugeStyle.MODERN:
        return _create_slider_modern(
            min=min,
            max=max,
            step=step,
            value=value,
            on_change=on_change,
        )

    if style in (GaugeStyle.RETRO, GaugeStyle.DEFAULT):
        return _create_slider_retro(
            min=min,
            max=max,
            step=step,
            value=value,
            on_change=on_change,
        )

    raise ValueError(f"Unsupported slider style: {style=}")


def create_label(
        style: GaugeStyle = GaugeStyle.MODERN,
        *,
        text: str = "",
):
    if style == GaugeStyle.MODERN:
        return _create_label_modern(text=text)

    if style == GaugeStyle.DEFAULT:
        return _create_label_default(text=text)

    if style == GaugeStyle.RETRO:
        return _create_label_retro(text=text)

    raise ValueError(f"Unsupported label style: {style=}")


def create_selection(
    style: GaugeStyle = GaugeStyle.MODERN,
    *,
    options: list[str],
    value: str | None = None,
    on_change=None,
):
    if style == GaugeStyle.MODERN:
        return _create_selection_modern(
            options=options,
            value=value,
            on_change=on_change,
        )

    if style in (GaugeStyle.RETRO, GaugeStyle.DEFAULT):
        return _create_selection_retro(
            options=options,
            value=value,
            on_change=on_change,
        )

    raise ValueError(f"Unsupported selection style: {style=}")


def create_generic_echart(
    style: GaugeStyle = GaugeStyle.MODERN,
    *,
    categories: list[str] | None = None,
    min_value: int = 0,
    max_value: int = 100,
):
    resolved_categories = categories or ["Actual", "Target"]

    if style == GaugeStyle.MODERN:
        return _create_generic_echart_modern(
            categories=resolved_categories,
            min_value=min_value,
            max_value=max_value,
        )

    if style in (GaugeStyle.RETRO, GaugeStyle.DEFAULT):
        return _create_generic_echart_retro(
            categories=resolved_categories,
            min_value=min_value,
            max_value=max_value,
        )

    raise ValueError(f"Unsupported echart style: {style=}")


def create_control_light(
    style: GaugeStyle = GaugeStyle.MODERN,
    *,
    value: bool = False,
    icon: ControlLightIcon = ControlLightIcon.NONE,
    size: int = 48,
    on_color: str = "#F5C542",
    off_color: str = "#2A2A2A",
):
    if style in (GaugeStyle.MODERN, GaugeStyle.RETRO, GaugeStyle.DEFAULT):
        return _create_control_light(
            value=value,
            icon=ControlLightIcon(icon),
            size=size,
            on_color=on_color,
            off_color=off_color,
        )

    raise ValueError(f"Unsupported control light style: {style=}")


def _create_control_light(
    *,
    value: bool,
    icon: ControlLightIcon,
    size: int,
    on_color: str,
    off_color: str,
):
    state = bool(value)

    def root_style() -> str:
        return (
            "display: inline-flex;"
            "align-items: center;"
            "justify-content: center;"
            f"width: {size}px;"
            f"height: {size}px;"
            "box-sizing: border-box;"
            "background: transparent;"
            "border: none;"
            "box-shadow: none;"
            "overflow: visible;"
        )

    def lamp_style(is_on: bool) -> str:
        color = on_color if is_on else off_color
        opacity = "1" if is_on else "0.32"

        if icon == ControlLightIcon.NONE:
            return (
                f"width: {size}px;"
                f"height: {size}px;"
                "border-radius: 9999px;"
                f"background: {color};"
                f"opacity: {opacity};"
                "border: none;"
                "box-shadow: none;"
                "transition: opacity 120ms ease, background 120ms ease;"
            )

        icon_path = _CONTROL_LIGHT_ICON_PATHS[icon]
        return (
            f"width: {size}px;"
            f"height: {size}px;"
            f"background: {color};"
            f"opacity: {opacity};"
            f"mask: url('{icon_path}') center / contain no-repeat;"
            f"-webkit-mask: url('{icon_path}') center / contain no-repeat;"
            "border: none;"
            "box-shadow: none;"
            "transition: opacity 120ms ease, background 120ms ease;"
        )

    with ui.element("div").style(root_style()) as control_light:
        lamp = ui.element("div").style(lamp_style(state))

    def apply(next_value: bool) -> None:
        next_state = bool(next_value)
        lamp.style(replace=lamp_style(next_state))
        control_light._control_light_value = next_state

    control_light._set_control_light_value = apply
    control_light._control_light_value = state

    return control_light


def _scaled(value: float, scale: float, minimum: int | None = None) -> int:
    result = int(round(value * scale))
    if minimum is not None:
        result = max(minimum, result)
    return result


def _create_generic_gauge_modern(
    *,
    min_value: int,
    max_value: int,
    split_number: int,
):
    return ui.echart(
        {
            "series": [
                {
                    "type": "gauge",
                    "startAngle": 180,
                    "endAngle": 0,
                    "center": ["50%", "72%"],
                    "radius": "85%",
                    "min": min_value,
                    "max": max_value,
                    "splitNumber": split_number,
                    "progress": {"show": True, "width": 18},
                    "axisLine": {"lineStyle": {"width": 18}},
                    "axisTick": {
                        "distance": -24,
                        "splitNumber": 5,
                        "lineStyle": {"width": 1},
                    },
                    "splitLine": {
                        "distance": -26,
                        "length": 12,
                        "lineStyle": {"width": 2},
                    },
                    "axisLabel": {"distance": -16, "fontSize": 12},
                    "anchor": {"show": True, "size": 10, "showAbove": True},
                    "pointer": {"width": 4},
                    "title": {"show": False},
                    "detail": {"show": False},
                    "data": [{"value": min_value}],
                }
            ]
        }
    ).classes("w-full h-80")


def _create_generic_gauge_retro(
    *,
    min_value: int,
    max_value: int,
    split_number: int,
    inner_background: str,
    size: int | None = None,
):
    baseline_size = 320
    effective_size = size or baseline_size
    scale = effective_size / baseline_size

    # Scale everything from one baseline so bezel, face, ticks, labels and pointer
    # stay aligned when the component becomes bigger/smaller.
    bezel_radius = _scaled(150, scale)
    face_radius = _scaled(142, scale)

    gauge_radius = _scaled(118, scale)

    axis_line_width = _scaled(14, scale, 8)
    tick_distance = -_scaled(38, scale, 14)
    tick_length = _scaled(20, scale, 10)
    tick_width = _scaled(4, scale, 2)

    label_distance = -_scaled(15, scale, 6)
    label_font_size = _scaled(20, scale, 12)

    anchor_size = _scaled(18, scale, 10)

    # Slightly bigger needle than before
    pointer_width = _scaled(8, scale, 4)
    pointer_length = "70%"

    return ui.echart(
        {
            "backgroundColor": "transparent",
            "graphic": [
                {
                    "type": "group",
                    "left": "center",
                    "top": "middle",
                    "bounding": "raw",
                    "z": 0,
                    "children": [
                        {
                            # bezel
                            "type": "circle",
                            "shape": {"cx": 0, "cy": 0, "r": bezel_radius},
                            "style": {
                                "fill": "#2B2E34",
                                "shadowBlur": _scaled(3, scale, 1),
                                "shadowColor": "rgba(0, 0, 0, 0.18)",
                            },
                        },
                        {
                            # dial face
                            "type": "circle",
                            "shape": {"cx": 0, "cy": 0, "r": face_radius},
                            "style": {
                                "fill": inner_background,
                            },
                        },
                    ],
                }
            ],
            "series": [
                {
                    "type": "gauge",
                    "center": ["50%", "50%"],
                    "radius": gauge_radius,
                    "startAngle": 225,
                    "endAngle": -45,
                    "min": min_value,
                    "max": max_value,
                    "splitNumber": split_number,
                    "progress": {"show": False},
                    "axisLine": {
                        "show": True,
                        "lineStyle": {
                            "width": axis_line_width,
                            "color": [[1, "#050505"]],
                        },
                    },
                    "axisTick": {
                        "show": True,
                        "distance": tick_distance,
                        "splitNumber": 1,
                        "length": tick_length,
                        "lineStyle": {
                            "width": tick_width,
                            "color": "#F2F2F2",
                        },
                    },
                    "splitLine": {
                        "show": False,
                    },
                    "axisLabel": {
                        "show": True,
                        "distance": label_distance,
                        "color": "#F2F2F2",
                        "fontSize": label_font_size,
                        "fontWeight": "400",
                        "fontFamily": "Bahnschrift Condensed, DIN Alternate, Arial Narrow, Liberation Sans Narrow, DejaVu Sans Condensed, sans-serif",
                    },
                    "anchor": {
                        "show": True,
                        "showAbove": True,
                        "size": anchor_size,
                        "itemStyle": {
                            "color": "#111111",
                            "borderColor": "#111111",
                            "borderWidth": _scaled(2, scale, 1),
                        },
                    },
                    "pointer": {
                        "icon": "path://M -3.2 96 L 0 -18 L 3.2 96 L 0 76 z",
                        "length": pointer_length,
                        "width": pointer_width,
                        "offsetCenter": [0, "0%"],
                        "itemStyle": {
                            "color": "#D62D2D",
                        },
                    },
                    "title": {"show": False},
                    "detail": {"show": False},
                    "data": [{"value": min_value}],
                }
            ],
        }
    ).style(f"width: {effective_size}px; height: {effective_size}px;")


def _create_speed_gauge_modern(show_readout: bool = False):
    return ui.echart(
        {
            "series": [
                {
                    "type": "gauge",
                    "min": 0,
                    "max": 260,
                    "splitNumber": 13,
                    "progress": {"show": True},
                    "axisLine": {"lineStyle": {"width": 18}},
                    "axisTick": {
                        "show": True,
                        "splitNumber": 4,
                    },
                    "splitLine": {
                        "show": True,
                        "length": 14,
                        "lineStyle": {"width": 2},
                    },
                    "axisLabel": {
                        "show": True,
                        "distance": 18,
                        "fontSize": 12,
                    },
                    "pointer": {
                        "show": True,
                    },
                    "anchor": {
                        "show": True,
                        "showAbove": True,
                        "size": 10,
                    },
                    "detail": {
                        "show": show_readout,
                        "valueAnimation": True,
                        "formatter": "{value} km/h",
                        "fontSize": 18,
                    },
                    "data": [{"value": 0}],
                }
            ]
        }
    ).classes("w-full h-96")


def _create_speed_gauge_retro_svg(
    show_readout: bool = False,
    show_scale_ring: bool = False,
):
    graphic_children = [
        {
            "type": "circle",
            "shape": {"cx": 0, "cy": 0, "r": 168},
            "style": {
                "fill": "#202020",
                "shadowBlur": 14,
                "shadowColor": "rgba(0, 0, 0, 0.35)",
            },
        },
        {
            "type": "circle",
            "shape": {"cx": 0, "cy": 0, "r": 160},
            "style": {
                "fill": "#050505",
            },
        },
    ]

    if show_scale_ring:
        graphic_children.append(
            {
                "type": "sector",
                "shape": {
                    "cx": 0,
                    "cy": 0,
                    "r": 156,
                    "r0": 152,
                    "startAngle": 0,
                    "endAngle": 6.28318530718,
                },
                "style": {
                    "fill": "#A9A9A9",
                    "opacity": 0.95,
                },
            }
        )

    graphic_children.extend(
        [
            {
                "type": "circle",
                "shape": {"cx": 0, "cy": 0, "r": 144},
                "style": {
                    "fill": "#000000",
                },
            },
            {
                "type": "image",
                "x": -170,
                "y": -162,
                "style": {
                    "image": _asset_path("retro_speed.svg"),
                    "width": 340,
                    "height": 324,
                    "opacity": 1,
                },
            },
        ]
    )

    return ui.echart(
        {
            "backgroundColor": "transparent",
            "graphic": [
                {
                    "type": "group",
                    "left": "center",
                    "top": "middle",
                    "bounding": "raw",
                    "z": 0,
                    "children": graphic_children,
                }
            ],
            "series": [
                {
                    "type": "gauge",
                    "center": ["50%", "50%"],
                    "radius": "83%",
                    "startAngle": 228,
                    "endAngle": -48,
                    "min": 0,
                    "max": 260,
                    "splitNumber": 13,
                    "progress": {"show": False},
                    "axisLine": {
                        "show": False,
                        "lineStyle": {
                            "width": 0,
                            "color": [[1, "rgba(0,0,0,0)"]],
                        },
                    },
                    "axisTick": {"show": False},
                    "splitLine": {"show": False},
                    "axisLabel": {"show": False},
                    "title": {"show": False},
                    "anchor": {
                        "show": True,
                        "showAbove": True,
                        "size": 22,
                        "itemStyle": {
                            "color": "#111111",
                            "borderColor": "#000000",
                            "borderWidth": 3,
                            "shadowBlur": 6,
                            "shadowColor": "rgba(0, 0, 0, 0.35)",
                        },
                    },
                    "pointer": {
                        "icon": "path://M -3.2 88 L 0 -18 L 3.2 88 L 0 74 z",
                        "length": "64%",
                        "width": 6,
                        "offsetCenter": [0, "0%"],
                        "itemStyle": {
                            "color": "#BE1E2D",
                            "shadowBlur": 3,
                            "shadowColor": "rgba(0, 0, 0, 0.25)",
                        },
                    },
                    "detail": {
                        "show": show_readout,
                        "valueAnimation": True,
                        "formatter": "{value} km/h",
                        "color": "#F2F2F2",
                        "fontSize": 18,
                        "fontWeight": "bold",
                        "offsetCenter": [0, "72%"],
                        "backgroundColor": "rgba(0, 0, 0, 0.38)",
                        "borderRadius": 6,
                        "padding": [4, 10, 4, 10],
                    },
                    "data": [{"value": 0}],
                }
            ],
        }
    ).classes("w-full h-96")


def _create_speed_gauge_default_svg(
    show_readout: bool = False,
    show_scale_ring: bool = False,
):
    # Velocity.svg: viewBox="0 0 469 467", scale 0-240 km/h.
    # Rendered at 310x310, centered at origin (x=-155, y=-155),
    # so it fits inside the black face circle (r=160) with a small margin.
    graphic_children = [
        {
            "type": "circle",
            "shape": {"cx": 0, "cy": 0, "r": 168},
            "style": {
                "fill": "#202020",
                "shadowBlur": 14,
                "shadowColor": "rgba(0, 0, 0, 0.35)",
            },
        },
        {
            "type": "circle",
            "shape": {"cx": 0, "cy": 0, "r": 160},
            "style": {
                "fill": "#050505",
            },
        },
    ]

    if show_scale_ring:
        graphic_children.append(
            {
                "type": "sector",
                "shape": {
                    "cx": 0,
                    "cy": 0,
                    "r": 156,
                    "r0": 152,
                    "startAngle": 0,
                    "endAngle": 6.28318530718,
                },
                "style": {
                    "fill": "#A9A9A9",
                    "opacity": 0.95,
                },
            }
        )

    graphic_children.extend(
        [
            {
                "type": "circle",
                "shape": {"cx": 0, "cy": 0, "r": 144},
                "style": {
                    "fill": "#000000",
                },
            },
            {
                "type": "image",
                "x": -155,
                "y": -155,
                "style": {
                    "image": _asset_path("Velocity.svg"),
                    "width": 310,
                    "height": 310,
                    "opacity": 1,
                },
            },
        ]
    )

    return ui.echart(
        {
            "backgroundColor": "transparent",
            "graphic": [
                {
                    "type": "group",
                    "left": "center",
                    "top": "middle",
                    "bounding": "raw",
                    "z": 0,
                    "children": graphic_children,
                }
            ],
            "series": [
                {
                    "type": "gauge",
                    "center": ["50%", "50%"],
                    "radius": "83%",
                    "startAngle": 198,
                    "endAngle": -18,
                    "min": 0,
                    "max": 240,
                    "splitNumber": 12,
                    "progress": {"show": False},
                    "axisLine": {
                        "show": False,
                        "lineStyle": {
                            "width": 0,
                            "color": [[1, "rgba(0,0,0,0)"]],
                        },
                    },
                    "axisTick": {"show": False},
                    "splitLine": {"show": False},
                    "axisLabel": {"show": False},
                    "title": {"show": False},
                    "anchor": {
                        "show": True,
                        "showAbove": True,
                        "size": 22,
                        "itemStyle": {
                            "color": "#111111",
                            "borderColor": "#000000",
                            "borderWidth": 3,
                            "shadowBlur": 6,
                            "shadowColor": "rgba(0, 0, 0, 0.35)",
                        },
                    },
                    "pointer": {
                        "icon": "path://M -3.2 88 L 0 -18 L 3.2 88 L 0 74 z",
                        "length": "64%",
                        "width": 6,
                        "offsetCenter": [0, "0%"],
                        "itemStyle": {
                            "color": "#BE1E2D",
                            "shadowBlur": 3,
                            "shadowColor": "rgba(0, 0, 0, 0.25)",
                        },
                    },
                    "detail": {
                        "show": show_readout,
                        "valueAnimation": True,
                        "formatter": "{value} km/h",
                        "color": "#F2F2F2",
                        "fontSize": 18,
                        "fontWeight": "bold",
                        "offsetCenter": [0, "72%"],
                        "backgroundColor": "rgba(0, 0, 0, 0.38)",
                        "borderRadius": 6,
                        "padding": [4, 10, 4, 10],
                    },
                    "data": [{"value": 0}],
                }
            ],
        }
    ).classes("w-full h-96")


def _create_torque_gauge_default_svg(
    show_readout: bool = False,
):
    # Drehmoment.svg: viewBox="0 0 467 322", gauge center at cx=233, cy=235.
    # RPM gauge (1/min×1000), labeled ticks 1-7 at rotate(-108) to rotate(108).
    # Each interval = 36°. Value 0 is one interval before "1":
    #   startAngle = 198 + 36 = 234, endAngle = -18, min=0, max=7.
    # Rendered at width=305, height=211 to stay inside black face (r=160):
    #   x = -(305*(233/467)) = -152, y = -(211*(235/322)) = -154.

    graphic_children = [
        {
            "type": "circle",
            "shape": {"cx": 0, "cy": 0, "r": 168},
            "style": {
                "fill": "#202020",
                "shadowBlur": 14,
                "shadowColor": "rgba(0, 0, 0, 0.35)",
            },
        },
        {
            "type": "circle",
            "shape": {"cx": 0, "cy": 0, "r": 160},
            "style": {
                "fill": "#050505",
            },
        },
        {
            "type": "image",
            "x": -152,
            "y": -154,
            "style": {
                "image": _asset_path("Drehmoment.svg"),
                "width": 305,
                "height": 211,
                "opacity": 1,
            },
        },
    ]

    return ui.echart(
        {
            "backgroundColor": "transparent",
            "graphic": [
                {
                    "type": "group",
                    "left": "center",
                    "top": "middle",
                    "bounding": "raw",
                    "z": 0,
                    "children": graphic_children,
                }
            ],
            "series": [
                {
                    "type": "gauge",
                    "center": ["50%", "50%"],
                    "radius": "83%",
                    "startAngle": 234,
                    "endAngle": -18,
                    "min": 0,
                    "max": 7,
                    "splitNumber": 7,
                    "progress": {"show": False},
                    "axisLine": {
                        "show": False,
                        "lineStyle": {
                            "width": 0,
                            "color": [[1, "rgba(0,0,0,0)"]],
                        },
                    },
                    "axisTick": {"show": False},
                    "splitLine": {"show": False},
                    "axisLabel": {"show": False},
                    "title": {"show": False},
                    "anchor": {
                        "show": True,
                        "showAbove": True,
                        "size": 22,
                        "itemStyle": {
                            "color": "#111111",
                            "borderColor": "#000000",
                            "borderWidth": 3,
                            "shadowBlur": 6,
                            "shadowColor": "rgba(0, 0, 0, 0.35)",
                        },
                    },
                    "pointer": {
                        "icon": "path://M -3.2 88 L 0 -18 L 3.2 88 L 0 74 z",
                        "length": "64%",
                        "width": 6,
                        "offsetCenter": [0, "0%"],
                        "itemStyle": {
                            "color": "#BE1E2D",
                            "shadowBlur": 3,
                            "shadowColor": "rgba(0, 0, 0, 0.25)",
                        },
                    },
                    "detail": {
                        "show": show_readout,
                        "valueAnimation": True,
                        "formatter": "{value} ×1000/min",
                        "color": "#F2F2F2",
                        "fontSize": 18,
                        "fontWeight": "bold",
                        "offsetCenter": [0, "72%"],
                        "backgroundColor": "rgba(0, 0, 0, 0.38)",
                        "borderRadius": 6,
                        "padding": [4, 10, 4, 10],
                    },
                    "data": [{"value": 0}],
                }
            ],
        }
    ).classes("w-full h-96")


def _create_fuel_gauge_default_svg(
    show_readout: bool = False,
):
    return ui.echart(
        {
            "backgroundColor": "transparent",
            "graphic": [
                {
                    "type": "group",
                    "left": "17%",
                    "top": "75%",
                    "bounding": "raw",
                    "z": 0,
                    "children": [
                        {
                            "type": "image",
                            "x": -21,
                            "y": -99,
                            "style": {
                                "image": _asset_path("Tank.svg"),
                                "width": 120,
                                "height": 145,
                                "opacity": 1,
                            },
                        }
                    ],
                }
            ],
            "series": [
                {
                    "type": "gauge",
                    "center": ["17%", "75%"],
                    "radius": 139,
                    "startAngle": 90,
                    "endAngle": -18,
                    "min": 0,
                    "max": 100,
                    "splitNumber": 6,
                    "progress": {"show": False},
                    "axisLine": {
                        "show": False,
                        "lineStyle": {
                            "width": 0,
                            "color": [[1, "rgba(0,0,0,0)"]],
                        },
                    },
                    "axisTick": {"show": False},
                    "splitLine": {"show": False},
                    "axisLabel": {"show": False},
                    "title": {"show": False},
                    "anchor": {
                        "show": True,
                        "showAbove": True,
                        "size": 13,
                        "itemStyle": {
                            "color": "#CDD0D3",
                            "borderColor": "#CDD0D3",
                            "borderWidth": 2,
                            "shadowBlur": 4,
                            "shadowColor": "rgba(0, 0, 0, 0.35)",
                        },
                    },
                    "pointer": {
                        "icon": "path://M -1.5 55 L 0 -8 L 1.5 55 L 0 45 z",
                        "length": "70%",
                        "width": 3,
                        "offsetCenter": [0, "0%"],
                        "itemStyle": {
                            "color": "#BE1E2D",
                            "shadowBlur": 3,
                            "shadowColor": "rgba(0, 0, 0, 0.25)",
                        },
                    },
                    "detail": {
                        "show": show_readout,
                        "valueAnimation": True,
                        "formatter": "{value}%",
                        "color": "#F2F2F2",
                        "fontSize": 14,
                        "fontWeight": "bold",
                        "offsetCenter": [120, -40],
                        "backgroundColor": "rgba(0, 0, 0, 0.38)",
                        "borderRadius": 6,
                        "padding": [4, 10, 4, 10],
                    },
                    "data": [{"value": 100}],
                }
            ],
        }
    ).classes("w-full h-56")


def _create_slider_modern(
    *,
    min: int,
    max: int,
    step: int,
    value: int,
    on_change=None,
):
    return ui.slider(
        min=min,
        max=max,
        step=step,
        value=value,
        on_change=on_change,
    ).classes("w-full")


def _create_slider_retro(
    *,
    min: int,
    max: int,
    step: int,
    value: int,
    on_change=None,
):
    slider_id = f"retro-slider-{next(_retro_slider_counter)}"

    with (
        ui.element("div")
        .classes(f"{slider_id} w-full")
        .style("display: flex; align-items: center;")
    ):
        ui.html(
            f"""
            <style>
                .{slider_id} .q-slider {{
                    padding: 10px 0;
                }}

                .{slider_id} .q-slider__track-container {{
                    height: 6px;
                }}

                .{slider_id} .q-slider__track {{
                    background: rgba(20, 20, 20, 0.85);
                }}

                .{slider_id} .q-slider__selection {{
                    background: #b3362d;
                }}

                .{slider_id} .q-slider__thumb-container {{
                    z-index: 2;
                }}

                .{slider_id} .q-slider__thumb {{
                    width: 18px !important;
                    height: 30px !important;
                    min-width: 18px !important;
                    min-height: 30px !important;
                    border-radius: 2px !important;
                    background: #cfcfcf !important;
                    color: #cfcfcf !important;
                    border: 2px solid #7f7f7f !important;
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.45) !important;
                }}

                .{slider_id} .q-slider__thumb-shape {{
                    display: none !important;
                }}

                .{slider_id} .q-slider__focus-ring {{
                    display: none !important;
                }}
            </style>
            """,
            sanitize=False,
        )

        slider = (
            ui.slider(
                min=min,
                max=max,
                step=step,
                value=value,
                on_change=on_change,
            )
            .props("color=red-8")
            .classes("w-full")
        )

    return slider


def _create_label_modern(*, text: str):
    return ui.label(text).classes(
        "min-w-[64px] text-center text-sm font-semibold px-3 py-2 rounded-md border border-gray-300 bg-gray-50 text-gray-800"
    )


def _create_label_default(*, text: str):
    return ui.label(text).style(
        "min-width: 64px;"
        "text-align: center;"
        "font-size: 0.95rem;"
        "font-weight: 600;"
        "padding: 6px 16px;"
        "border-radius: 4px;"
        "border: 1px solid rgba(255, 255, 255, 0.12);"
        "background: rgba(255, 255, 255, 0.06);"
        "color: #F2F2F2;"
        "letter-spacing: 0.03em;"
        "width: 100%;"
        "box-sizing: border-box;"
    )


def _create_label_retro(*, text: str):
    return ui.label(text).style(
        "min-width: 64px;"
        "text-align: center;"
        "font-size: 0.95rem;"
        "font-weight: 400;"
        "padding: 6px 16px;"
        "border-radius: 2px;"
        "border: 1px solid rgba(255, 255, 255, 0.15);"
        "background: rgba(10, 10, 10, 0.55);"
        "color: #CFCFCF;"
        "font-family: Bahnschrift Condensed, DIN Alternate, Arial Narrow, sans-serif;"
        "letter-spacing: 0.05em;"
        "width: 100%;"
        "box-sizing: border-box;"
    )


def _create_selection_modern(
    *,
    options: list[str],
    value: str | None,
    on_change=None,
):
    return ui.select(
        options=options,
        value=value,
        on_change=on_change,
    ).classes("w-full")


def _create_selection_retro(
    *,
    options: list[str],
    value: str | None,
    on_change=None,
):
    # TODO: Implement a truly retro selection control
    return _create_selection_modern(
        options=options,
        value=value,
        on_change=on_change,
    )


def _create_generic_echart_modern(
    *,
    categories: list[str],
    min_value: int,
    max_value: int,
):
    palette = ["#5B8CFF", "#FFB020", "#34C759", "#AF52DE", "#FF3B30"]

    return ui.echart(
        {
            "grid": {
                "left": "12%",
                "right": "10%",
                "top": "12%",
                "bottom": "12%",
                "containLabel": True,
            },
            "xAxis": {
                "type": "value",
                "min": min_value,
                "max": max_value,
                "axisLabel": {"formatter": "{value}"},
            },
            "yAxis": {
                "type": "category",
                "data": categories,
                "axisTick": {"show": False},
            },
            "series": [
                {
                    "type": "bar",
                    "barWidth": 24,
                    "showBackground": True,
                    "backgroundStyle": {"color": "rgba(180, 180, 180, 0.15)"},
                    "label": {
                        "show": True,
                        "position": "right",
                        "fontSize": 16,
                        "fontWeight": "bold",
                    },
                    "data": [
                        {
                            "value": 0,
                            "itemStyle": {"color": palette[index % len(palette)]},
                        }
                        for index, _ in enumerate(categories)
                    ],
                }
            ],
        }
    ).classes("w-full h-64")


def _create_generic_echart_retro(
    *,
    categories: list[str],
    min_value: int,
    max_value: int,
):
    return _create_generic_echart_modern(
        categories=categories,
        min_value=min_value,
        max_value=max_value,
    )


def set_control_light_value(control_light, value: bool) -> None:
    apply = getattr(control_light, "_set_control_light_value", None)

    if apply is None:
        raise ValueError("Expected a control light created by create_control_light().")

    apply(bool(value))


def set_gauge_value(chart, value: int, *, invert: bool = False) -> None:
    series = chart.options["series"][0]
    internal = int(series["max"]) - int(value) if invert else int(value)
    series["data"][0]["value"] = internal
    chart.update()


def set_generic_echart_values(chart, values: list[int]) -> None:
    for index, value in enumerate(values):
        chart.options["series"][0]["data"][index]["value"] = int(value)
    chart.update()
