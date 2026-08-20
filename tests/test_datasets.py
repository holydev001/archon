from datetime import UTC, datetime, timedelta

import pytest

from archon.datasets import chronological_split, load_bars_csv
from archon.domain import Bar


def test_loads_csv_with_utf8_bom_and_optional_spread(tmp_path) -> None:
    path = tmp_path / "bars.csv"
    path.write_text(
        "\ufeffsymbol,timestamp,open,high,low,close\n"
        "EURUSD,2026-01-01T00:00:00Z,1.1,1.2,1.0,1.15\n",
        encoding="utf-8",
    )
    bars = load_bars_csv(path)
    assert len(bars) == 1
    assert bars[0].spread == 0


def test_reports_csv_line_for_invalid_data(tmp_path) -> None:
    path = tmp_path / "bars.csv"
    path.write_text(
        "symbol,timestamp,open,high,low,close\nEURUSD,bad,1,1,1,1\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="line 2"):
        load_bars_csv(path)


def test_split_keeps_equal_timestamps_in_test_partition() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    bars = [
        Bar(symbol, start + timedelta(minutes=minute), 1, 1, 1, 1)
        for minute, symbol in [(0, "EURUSD"), (1, "EURUSD"), (1, "GBPUSD"), (2, "EURUSD")]
    ]
    train, test = chronological_split(bars, 0.5)
    assert len(train) == 1
    assert all(bar.timestamp > train[-1].timestamp for bar in test)
