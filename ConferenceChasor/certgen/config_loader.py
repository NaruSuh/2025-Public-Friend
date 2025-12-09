from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class EventConfig:
    title: str
    subtitle: str | None = None
    description: str | None = None
    footer_note: str | None = None
    signature_block: list[dict[str, str]] = field(default_factory=list)
    date_label: str = "Date"


@dataclass
class LayoutConfig:
    page_orientation: str = "landscape"
    border_color: str = "#1f4b99"
    accent_color: str = "#004b7c"
    background_color: str = "#f7f9fc"
    font: dict[str, str] = field(
        default_factory=lambda: {"heading": "Helvetica-Bold", "body": "Helvetica"}
    )


@dataclass
class ColumnConfig:
    name: str = "Full Name"
    affiliation: str = "Affiliation"
    email: str | None = None
    completion_date: str | None = None
    status: str | None = None


@dataclass
class FilterConfig:
    column: str | None = None
    equals: str | None = None


@dataclass
class OutputConfig:
    dirname: str = "output"
    filename_pattern: str = "{name}_{event}.pdf"


@dataclass
class InputConfig:
    sheet_name: str | None = None
    date_format: str = "%Y-%m-%d"
    locale: str = ""


@dataclass
class AppConfig:
    event: EventConfig
    layout: LayoutConfig
    columns: ColumnConfig
    filters: FilterConfig
    output: OutputConfig
    input: InputConfig


DEFAULT_CONFIG = AppConfig(
    event=EventConfig(
        title="Conference",
        subtitle="",
        description="This certifies participation in the event listed below.",
        footer_note="",
        date_label="Issued"
    ),
    layout=LayoutConfig(),
    columns=ColumnConfig(),
    filters=FilterConfig(),
    output=OutputConfig(),
    input=InputConfig(),
)


def load_config(path: Optional[str]) -> AppConfig:
    if path is None:
        return merge_config({})

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as fh:
        data: Dict[str, Any] = yaml.safe_load(fh) or {}

    return merge_config(data)


def merge_config(raw: Dict[str, Any]) -> AppConfig:
    def nested_dataclass(default_obj: Any, payload: Dict[str, Any] | None):
        values: Dict[str, Any] = dict(default_obj.__dict__)
        if payload:
            values.update(payload)
        return default_obj.__class__(**values)

    return AppConfig(
        event=nested_dataclass(DEFAULT_CONFIG.event, raw.get("event")),
        layout=nested_dataclass(DEFAULT_CONFIG.layout, raw.get("layout")),
        columns=nested_dataclass(DEFAULT_CONFIG.columns, raw.get("columns")),
        filters=nested_dataclass(DEFAULT_CONFIG.filters, raw.get("filters")),
        output=nested_dataclass(DEFAULT_CONFIG.output, raw.get("output")),
        input=nested_dataclass(DEFAULT_CONFIG.input, raw.get("input")),
    )
