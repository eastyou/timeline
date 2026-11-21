from __future__ import annotations

"""历史事件时间轴：把 CSV 事件整理成可打印的 A4 时间轴。"""

from .cli import main
from .model import (
    Event,
    TimelineError,
    demo_events,
    filter_events,
    paginate,
    parse_csv_text,
    position_ratio,
    read_csv,
    year_range,
)
from .render import render_empty, render_timeline

__version__ = "0.1.0"

__all__ = [
    "Event",
    "TimelineError",
    "demo_events",
    "filter_events",
    "main",
    "paginate",
    "parse_csv_text",
    "position_ratio",
    "read_csv",
    "render_empty",
    "render_timeline",
    "year_range",
    "__version__",
]
