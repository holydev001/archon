from dataclasses import dataclass, field

from archon.domain import Bar, OrderIntent, Side


@dataclass(frozen=True, slots=True)
class Fill:
    symbol: str
    side: Side
    quantity: float
    entry_price: float
    exit_price: float
    gross_pnl: float
    costs: float
    net_pnl: float
    exit_reason: str


@dataclass(slots=True)
class PaperBroker:
    """Single-position paper executor with explicit spread, slippage, and commission."""

    balance: float
    slippage: float = 0.00002
    commission_per_unit: float = 0.0
    position: OrderIntent | None = None
    fills: list[Fill] = field(default_factory=list)

    def submit(self, order: OrderIntent) -> None:
        if self.position is not None:
            raise RuntimeError("paper broker already has an open position")
        adjusted_entry = order.entry_price + self.slippage * (1 if order.side is Side.BUY else -1)
        self.position = OrderIntent(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            entry_price=adjusted_entry,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            created_at=order.created_at,
        )

    def on_bar(self, bar: Bar) -> Fill | None:
        order = self.position
        if order is None or order.symbol != bar.symbol:
            return None
        exit_price: float | None = None
        reason = ""
        # Conservative rule: if stop and target occur within one bar, assume stop was first.
        if order.side is Side.BUY:
            if bar.low <= order.stop_loss:
                exit_price, reason = order.stop_loss - self.slippage, "stop_loss"
            elif bar.high >= order.take_profit:
                exit_price, reason = order.take_profit - self.slippage, "take_profit"
        else:
            if bar.high >= order.stop_loss:
                exit_price, reason = order.stop_loss + self.slippage, "stop_loss"
            elif bar.low <= order.take_profit:
                exit_price, reason = order.take_profit + self.slippage, "take_profit"
        if exit_price is None:
            return None
        return self._close(exit_price, reason)

    def close_at_market(self, price: float, reason: str = "end_of_data") -> Fill | None:
        """Close an open position conservatively at a supplied bid/ask-neutral price."""
        order = self.position
        if order is None:
            return None
        exit_price = price - self.slippage if order.side is Side.BUY else price + self.slippage
        return self._close(exit_price, reason)

    def _close(self, exit_price: float, reason: str) -> Fill:
        order = self.position
        if order is None:
            raise RuntimeError("cannot close without an open position")
        direction = 1 if order.side is Side.BUY else -1
        gross = (exit_price - order.entry_price) * direction * order.quantity
        costs = order.quantity * self.commission_per_unit
        fill = Fill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            entry_price=order.entry_price,
            exit_price=exit_price,
            gross_pnl=gross,
            costs=costs,
            net_pnl=gross - costs,
            exit_reason=reason,
        )
        self.balance += fill.net_pnl
        self.fills.append(fill)
        self.position = None
        return fill
