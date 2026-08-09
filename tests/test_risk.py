from datetime import UTC, datetime

from archon.domain import OrderIntent, Side
from archon.risk import AccountState, RiskGate, RiskLimits


def make_order(quantity: float = 1_000.0) -> OrderIntent:
    return OrderIntent(
        symbol="EURUSD",
        side=Side.BUY,
        quantity=quantity,
        entry_price=1.1000,
        stop_loss=1.0990,
        take_profit=1.1020,
        created_at=datetime.now(UTC),
    )


def test_approves_order_within_limits() -> None:
    result = RiskGate(RiskLimits()).evaluate(
        make_order(), AccountState(balance=10_000, equity=10_000), spread=0.0001
    )
    assert result.approved


def test_rejects_oversized_order() -> None:
    result = RiskGate(RiskLimits()).evaluate(
        make_order(quantity=100_000), AccountState(balance=10_000, equity=10_000), spread=0.0001
    )
    assert not result.approved
    assert "per-trade" in result.reason


def test_rejects_daily_loss_limit() -> None:
    result = RiskGate(RiskLimits()).evaluate(
        make_order(),
        AccountState(balance=10_000, equity=9_800, daily_realized_pnl=-200),
        spread=0.0001,
    )
    assert not result.approved
    assert "daily loss" in result.reason

