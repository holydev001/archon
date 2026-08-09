from datetime import UTC, datetime

from archon.domain import Bar, OrderIntent, Side
from archon.simulation import PaperBroker

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_buy_take_profit_includes_slippage_and_commission() -> None:
    broker = PaperBroker(balance=10_000, slippage=0.0001, commission_per_unit=0.00001)
    broker.submit(OrderIntent("EURUSD", Side.BUY, 1_000, 1.1000, 1.0990, 1.1020, NOW))
    fill = broker.on_bar(Bar("EURUSD", NOW, 1.1010, 1.1030, 1.1005, 1.1025))
    assert fill is not None
    assert fill.exit_reason == "take_profit"
    assert round(fill.net_pnl, 6) == 1.79
    assert broker.balance == 10_000 + fill.net_pnl


def test_stop_wins_when_stop_and_target_are_in_same_bar() -> None:
    broker = PaperBroker(balance=10_000, slippage=0)
    broker.submit(OrderIntent("EURUSD", Side.BUY, 1_000, 1.1000, 1.0990, 1.1020, NOW))
    fill = broker.on_bar(Bar("EURUSD", NOW, 1.1000, 1.1030, 1.0980, 1.1005))
    assert fill is not None
    assert fill.exit_reason == "stop_loss"
    assert round(fill.net_pnl, 6) == -1.0

