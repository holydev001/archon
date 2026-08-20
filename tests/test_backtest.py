from datetime import UTC, datetime, timedelta

import pytest

from archon.backtest import Backtester, calculate_metrics
from archon.config import BotConfig
from archon.domain import Bar, Side
from archon.simulation import Fill
from archon.strategy import MovingAverageConfig


def make_bars(prices: list[float]) -> list[Bar]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        Bar(
            "EURUSD",
            start + timedelta(minutes=index),
            price,
            price + 0.002,
            price - 0.002,
            price,
            0.0001,
        )
        for index, price in enumerate(prices)
    ]


def test_backtest_is_reproducible_and_closes_open_position() -> None:
    config = BotConfig(
        symbols=("EURUSD",),
        slippage=0,
        strategy=MovingAverageConfig(2, 4, 0.00001),
    )
    bars = make_bars([1.004, 1.003, 1.002, 1.001, 1.006])
    first = Backtester(config).run(bars)
    second = Backtester(config).run(reversed(bars))
    assert first.to_dict() == second.to_dict()
    assert first.metrics.total_trades == 1
    assert first.fills[0].exit_reason == "end_of_data"


def test_rejects_duplicate_bars() -> None:
    config = BotConfig(symbols=("EURUSD",))
    bars = make_bars([1.0])
    with pytest.raises(ValueError, match="duplicate bar"):
        Backtester(config).run([bars[0], bars[0]])


def test_calculates_drawdown_and_trade_statistics() -> None:
    fills = tuple(
        Fill("EURUSD", Side.BUY, 1, 1, 1, pnl, 0, pnl, "test")
        for pnl in (100.0, -50.0, -100.0, 200.0)
    )
    metrics = calculate_metrics(1_000, fills, [1_000, 1_100, 1_050, 950, 1_150])
    assert metrics.net_profit == 150
    assert metrics.win_rate == 0.5
    assert metrics.profit_factor == 2
    assert metrics.max_drawdown == 150
    assert metrics.max_drawdown_fraction == pytest.approx(150 / 1_100)


def test_writes_machine_readable_reports(tmp_path) -> None:
    config = BotConfig(
        symbols=("EURUSD",), slippage=0,
        strategy=MovingAverageConfig(2, 4, 0.00001),
    )
    result = Backtester(config).run(make_bars([1.004, 1.003, 1.002, 1.001, 1.006]))
    result.write_json(tmp_path / "result.json")
    result.write_trades_csv(tmp_path / "trades.csv")
    assert '"total_trades": 1' in (tmp_path / "result.json").read_text()
    assert "exit_reason" in (tmp_path / "trades.csv").read_text()
