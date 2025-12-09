from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import pandas as pd

from .config_loader import AppConfig


@dataclass
class Participant:
    name: str
    affiliation: str | None
    email: str | None
    completion_date: str | None
    raw: dict


class SheetLoader:
    def __init__(self, config: AppConfig):
        self.config = config

    def load(self, sheet_path: str) -> List[Participant]:
        path = Path(sheet_path)
        if not path.exists():
            raise FileNotFoundError(f"Sheet not found: {sheet_path}")

        if path.suffix.lower() in {".xlsx", ".xls", ".xlsm"}:
            sheet_name = 0 if self.config.input.sheet_name is None else self.config.input.sheet_name
            df = pd.read_excel(path, sheet_name=sheet_name)
            if isinstance(df, dict):
                # pandas returns a dict when sheet_name=None; take the first sheet consistently
                df = next(iter(df.values()))
        else:
            df = pd.read_csv(path)

        required = [self.config.columns.name]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required column(s): {', '.join(missing)}")

        if self.config.filters.column and self.config.filters.equals is not None:
            filter_col = self.config.filters.column
            if filter_col not in df.columns:
                raise ValueError(f"Filter column '{filter_col}' not found in sheet")
            df = df[df[filter_col] == self.config.filters.equals]

        participants: List[Participant] = []
        for _, row in df.iterrows():
            name = str(row.get(self.config.columns.name, "")).strip()
            if not name:
                continue
            participant = Participant(
                name=name,
                affiliation=_clean(row.get(self.config.columns.affiliation)),
                email=_clean(row.get(self.config.columns.email)),
                completion_date=_clean(row.get(self.config.columns.completion_date)),
                raw=row.to_dict(),
            )
            participants.append(participant)
        return participants


def _clean(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    return text or None
