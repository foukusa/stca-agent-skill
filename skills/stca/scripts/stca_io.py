"""Strict CSV input adapter; preserve every field before explicit numeric parsing.

This adapter does not preprocess chemical structures, select rows, or modify the
author's STCA algorithm. Shared by the runtime, dataset audit and joint screening.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path


CSV_POLICY = "strict_record_width_all_fields_text_v1"


def read_csv_records(path):
    path = Path(path).expanduser().resolve()
    raw = path.read_bytes()
    try:
        records = list(csv.reader(io.StringIO(raw.decode("utf-8-sig")), strict=True))
    except (UnicodeError, csv.Error) as exc:
        raise ValueError(f"Cannot read UTF-8 CSV: {exc}") from exc
    if not records or not records[0]:
        raise ValueError("CSV has no header.")
    header = records[0]
    if len(set(header)) != len(header) or any(not value.strip() for value in header):
        raise ValueError("CSV headers must be distinct and nonempty.")
    malformed = [i for i, row in enumerate(records[1:]) if len(row) != len(header)]
    if malformed:
        raise ValueError(
            "CSV records have the wrong column count at zero-based positions "
            f"{malformed[:5]}; no fields were shifted or dropped."
        )
    return path, raw, header, [dict(zip(header, row)) for row in records[1:]]


def read_csv_frame(path):
    import pandas as pd

    _, _, header, records = read_csv_records(path)
    if not records:
        raise ValueError("CSV contains no data records.")
    # DataFrame construction avoids pandas read_csv's implicit index detection
    # and numeric coercion of identifiers such as 001. STCA explicitly converts
    # the target and selected binary feature columns in its existing validators.
    return pd.DataFrame(records, columns=header, dtype=str)
