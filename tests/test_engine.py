from datetime import UTC, datetime, timedelta

from archon.config import BotConfig
from archon.domain import Bar
from archon.engine import PaperTradingEngine
from archon.strategy import MovingAverageConfig


def test_engine_routes_signal_through_risk_gate() -> None:
    config = BotConfig(
        symbols=("EURUSD",),
        strategy=MovingAverageConfig(fast_window=2, slow_window=4, min_separation_fraction=0.00001),
    )
    engine = PaperTradingEngine(config)
    prices = [1.004, 1.003, 1.002, 1.001, 1.006]
    events = []
    for index, price in enumerate(prices):
        events.extend(
            engine.on_bar(
                Bar(
                    "EURUSD",
                    datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=index),
                    price,
                    price + 0.0001,
                    price - 0.0001,
                    price,
                    0.0001,
                )
            )
        )
    assert [event.kind for event in events] == ["signal", "risk"]
    assert engine.broker.position is not None
