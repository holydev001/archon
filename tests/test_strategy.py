from datetime import datetime, timedelta, timezone

from archon.domain import Bar, Side
from archon.strategy import MovingAverageConfig, MovingAverageCrossStrategy


def bar(index: int, close: float) -> Bar:
    return Bar(
        symbol="EURUSD",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=index),
        open=close,
        high=close + 0.0001,
        low=close - 0.0001,
        close=close,
    )


def test_emits_buy_only_after_upward_cross() -> None:
    strategy = MovingAverageCrossStrategy(
        MovingAverageConfig(fast_window=2, slow_window=4, min_separation_fraction=0.00001)
    )
    signals = [strategy.on_bar(bar(i, price)) for i, price in enumerate([1.004, 1.003, 1.002, 1.001, 1.006])]
    assert signals[-1] is not None
    assert signals[-1].side is Side.BUY


def test_warmup_does_not_emit() -> None:
    strategy = MovingAverageCrossStrategy(MovingAverageConfig(fast_window=2, slow_window=4))
    assert all(strategy.on_bar(bar(i, 1.0)) is None for i in range(3))
