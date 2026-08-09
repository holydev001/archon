from dataclasses import dataclass

from archon.domain import OrderIntent, Side


@dataclass(frozen=True, slots=True)
class AccountState:
    balance: float
    equity: float
    daily_realized_pnl: float = 0.0
    open_positions: int = 0


@dataclass(frozen=True, slots=True)
class RiskLimits:
    risk_per_trade_fraction: float = 0.0025
    max_daily_loss_fraction: float = 0.02
    max_drawdown_fraction: float = 0.05
    max_open_positions: int = 1
    max_spread: float = 0.00025


@dataclass(frozen=True, slots=True)
class RiskDecision:
    approved: bool
    reason: str


class RiskGate:
    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits

    def evaluate(self, order: OrderIntent, account: AccountState, spread: float) -> RiskDecision:
        if account.balance <= 0 or account.equity <= 0:
            return RiskDecision(False, "account balance and equity must be positive")
        if order.quantity <= 0 or order.risk_per_unit <= 0:
            return RiskDecision(False, "order quantity and stop distance must be positive")
        if account.open_positions >= self.limits.max_open_positions:
            return RiskDecision(False, "maximum open positions reached")
        if spread > self.limits.max_spread:
            return RiskDecision(False, "spread exceeds configured maximum")
        if account.daily_realized_pnl <= -(account.balance * self.limits.max_daily_loss_fraction):
            return RiskDecision(False, "daily loss limit reached")
        drawdown = max(0.0, (account.balance - account.equity) / account.balance)
        if drawdown >= self.limits.max_drawdown_fraction:
            return RiskDecision(False, "drawdown limit reached")
        monetary_risk = order.risk_per_unit * order.quantity
        if monetary_risk > account.equity * self.limits.risk_per_trade_fraction:
            return RiskDecision(False, "order exceeds per-trade risk budget")
        if order.side is Side.BUY and not order.stop_loss < order.entry_price < order.take_profit:
            return RiskDecision(False, "invalid buy stop or target")
        if order.side is Side.SELL and not order.take_profit < order.entry_price < order.stop_loss:
            return RiskDecision(False, "invalid sell stop or target")
        return RiskDecision(True, "approved")

    def size_for_stop(self, equity: float, stop_distance: float) -> float:
        if equity <= 0 or stop_distance <= 0:
            raise ValueError("equity and stop distance must be positive")
        return (equity * self.limits.risk_per_trade_fraction) / stop_distance

