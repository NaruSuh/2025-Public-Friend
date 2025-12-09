from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.pdfgen import canvas

from .config_loader import AppConfig
from .data_loader import Participant


class CertificateGenerator:
    def __init__(self, config: AppConfig):
        self.config = config
        self.page_size = (
            landscape(A4)
            if self.config.layout.page_orientation.lower() == "landscape"
            else portrait(A4)
        )

    def build_all(self, participants: Iterable[Participant], dest_dir: Path) -> list[Path]:
        dest_dir.mkdir(parents=True, exist_ok=True)
        created: list[Path] = []
        for participant in participants:
            filename = self._build_filename(participant)
            output_path = dest_dir / filename
            self.build_single(participant, output_path)
            created.append(output_path)
        return created

    def build_single(self, participant: Participant, output_path: Path) -> None:
        c = canvas.Canvas(str(output_path), pagesize=self.page_size)
        width, height = self.page_size

        self._draw_background(c, width, height)
        self._draw_header(c, width, height)
        self._draw_body(c, participant, width, height)
        self._draw_footer(c, participant, width)

        c.showPage()
        c.save()

    def _draw_background(self, c: canvas.Canvas, width: float, height: float) -> None:
        bg = self._color(self.config.layout.background_color)
        c.setFillColor(bg)
        c.rect(0, 0, width, height, fill=1, stroke=0)

        border_color = self._color(self.config.layout.border_color)
        c.setStrokeColor(border_color)
        c.setLineWidth(6)
        margin = 18
        c.rect(margin, margin, width - 2 * margin, height - 2 * margin, fill=0)

    def _draw_header(self, c: canvas.Canvas, width: float, height: float) -> None:
        accent = self._color(self.config.layout.accent_color)
        c.setFillColor(accent)
        c.rect(0, height - 70, width, 70, fill=1, stroke=0)

        c.setFillColor(colors.white)
        c.setFont(self.config.layout.font.get("heading", "Helvetica-Bold"), 32)
        c.drawCentredString(width / 2, height - 45, self.config.event.title)

        if self.config.event.subtitle:
            c.setFont(self.config.layout.font.get("body", "Helvetica"), 16)
            c.drawCentredString(width / 2, height - 65, self.config.event.subtitle)

    def _draw_body(
        self,
        c: canvas.Canvas,
        participant: Participant,
        width: float,
        height: float,
    ) -> None:
        y = height - 150
        c.setFillColor(colors.HexColor("#333333"))
        c.setFont(self.config.layout.font.get("body", "Helvetica"), 16)
        description = self.config.event.description or "This certifies that"
        c.drawCentredString(width / 2, y, description)

        c.setFont(self.config.layout.font.get("heading", "Helvetica-Bold"), 42)
        c.drawCentredString(width / 2, y - 60, participant.name)

        y -= 120
        if participant.affiliation:
            c.setFont(self.config.layout.font.get("body", "Helvetica"), 18)
            c.drawCentredString(width / 2, y, participant.affiliation)
            y -= 40

        date_label = self.config.event.date_label or "Date"
        date_value = self._format_date(participant.completion_date)
        c.setFont(self.config.layout.font.get("body", "Helvetica"), 15)
        c.drawCentredString(width / 2, y, f"{date_label}: {date_value}")

    def _draw_footer(self, c: canvas.Canvas, participant: Participant, width: float) -> None:
        y_base = 120
        footnote = self.config.event.footer_note
        if footnote:
            c.setFont(self.config.layout.font.get("body", "Helvetica"), 14)
            c.setFillColor(colors.HexColor("#333333"))
            c.drawCentredString(width / 2, y_base + 40, footnote)

        signatures = self.config.event.signature_block or []
        if signatures:
            spacing = width / (len(signatures) + 1)
            for idx, block in enumerate(signatures, start=1):
                x = spacing * idx
                c.line(x - 120, y_base + 10, x + 120, y_base + 10)
                c.setFont(self.config.layout.font.get("body", "Helvetica"), 14)
                if block.get("label"):
                    c.drawCentredString(x, y_base + 20, block["label"])
                if block.get("name"):
                    c.drawCentredString(x, y_base - 5, block["name"])

    def _build_filename(self, participant: Participant) -> str:
        pattern = self.config.output.filename_pattern
        safe_name = participant.name.replace(" ", "_")
        event_name = self.config.event.title.replace(" ", "_")
        filename = pattern.format(name=safe_name, event=event_name)
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        return filename

    def _format_date(self, value: str | None) -> str:
        fmt = self.config.input.date_format or "%Y-%m-%d"
        if not value:
            return datetime.now().strftime(fmt)
        try:
            dt = pd.to_datetime(value)
            return dt.strftime(fmt)
        except Exception:
            return str(value)

    @staticmethod
    def _color(value: str) -> colors.Color:
        try:
            return colors.HexColor(value)
        except Exception:  # pragma: no cover - fallback
            return colors.HexColor("#1f4b99")
