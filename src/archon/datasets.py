import csv
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from archon.domain import Bar

REQUIRED_COLUMNS = {"symbol", "timestamp", "open", "high", "low", "close"}


def load_bars_csv(path: str | Path) -> list[Bar]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")
        bars = [_parse_bar(row, line_number) for line_number, row in enumerate(reader, start=2)]
    if not bars:
        raise ValueError("CSV contains no bars")
    return bars


def chronological_split(bars: Iterable[Bar], train_fraction: float) -> tuple[list[Bar], list[Bar]]:
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    ordered = sorted(bars, key=lambda bar: (bar.timestamp, bar.symbol))
    if len(ordered) < 2:
        raise ValueError("at least two bars are required for a split")
    split_index = min(len(ordered) - 1, max(1, round(len(ordered) * train_fraction)))
    boundary = ordered[split_index].timestamp
    while split_index > 0 and ordered[split_index - 1].timestamp == boundary:
        split_index -= 1
    if split_index == 0:
        raise ValueError("cannot split data containing only one timestamp")
    return ordered[:split_index], ordered[split_index:]


def _parse_bar(row: dict[str, str], line_number: int) -> Bar:
    try:
        return Bar(
            symbol=row["symbol"].strip(),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            spread=float(row.get("spread") or 0.0),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid CSV bar at line {line_number}: {exc}") from exc
