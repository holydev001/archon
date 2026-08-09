from dataclasses import dataclass
from datetime import date

from archon.config import BotConfig
from archon.domain import Bar, OrderIntent, Side
from archon.risk import AccountState, RiskDecision, RiskGate
from archon.simulation import Fill, PaperBroker
from archon.strategy import MovingAverageCrossStrategy


@dataclass(frozen=True, slots=True)
class EngineEvent:
    kind: str
    message: str


class PaperTradingEngine:
    def __init__(self, config: BotConfig) -> None:
        self.config = config
        self.strategies = {
            symbol: MovingAverageCrossStrategy(config.strategy) for symbol in config.symbols
        }
        self.risk = RiskGate(config.risk)
        self.broker = PaperBroker(
            balance=config.initial_balance,
            slippage=config.slippage,
            commission_per_unit=config.commission_per_unit,
        )
        self._trading_day: date | None = None
        self._daily_realized_pnl = 0.0

    def on_bar(self, bar: Bar) -> list[EngineEvent]:
        if bar.symbol not in self.strategies:
            return [EngineEvent("ignored", f"symbol not enabled: {bar.symbol}")]
        self._roll_day(bar.timestamp.date())
        events: list[EngineEvent] = []
        fill = self.broker.on_bar(bar)
        if fill:
            self._daily_realized_pnl += fill.net_pnl
            events.append(self._fill_event(fill))
        if self.broker.position is not None:
            return events
        signal = self.strategies[bar.symbol].on_bar(bar)
        if signal is None:
            return events
        events.append(EngineEvent("signal", signal.reason))
        stop = bar.close - self.config.stop_distance if signal.side is Side.BUY else bar.close + self.config.stop_distance
        target_distance = self.config.stop_distance * self.config.reward_risk_ratio
        target = bar.close + target_distance if signal.side is Side.BUY else bar.close - target_distance
        quantity = self.risk.size_for_stop(self.broker.balance, self.config.stop_distance)
        order = OrderIntent(bar.symbol, signal.side, quantity, bar.close, stop, target, bar.timestamp)
        decision = self.risk.evaluate(order, self._account_state(), bar.spread)
        events.append(self._decision_event(decision))
        if decision.approved:
            self.broker.submit(order)
        return events

    def _account_state(self) -> AccountState:
        return AccountState(
            balance=self.broker.balance,
            equity=self.broker.balance,
            daily_realized_pnl=self._daily_realized_pnl,
            open_positions=int(self.broker.position is not None),
        )

    def _roll_day(self, current: date) -> None:
        if current != self._trading_day:
            self._trading_day = current
            self._daily_realized_pnl = 0.0

    @staticmethod
    def _fill_event(fill: Fill) -> EngineEvent:
        return EngineEvent("fill", f"{fill.exit_reason}: net_pnl={fill.net_pnl:.6f}")

    @staticmethod
    def _decision_event(decision: RiskDecision) -> EngineEvent:
        return EngineEvent("risk", f"{'approved' if decision.approved else 'rejected'}: {decision.reason}")

