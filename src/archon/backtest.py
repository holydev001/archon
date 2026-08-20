import csv
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime
from math import sqrt
from pathlib import Path
from statistics import mean, pstdev

from archon.config import BotConfig
from archon.domain import Bar
from archon.engine import PaperTradingEngine
from archon.simulation import Fill


@dataclass(frozen=True, slots=True)
class BacktestMetrics:
    initial_balance: float
    final_balance: float
    net_profit: float
    return_fraction: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float | None
    average_trade: float
    max_drawdown: float
    max_drawdown_fraction: float
    payoff_ratio: float | None
    trade_sharpe: float | None


@dataclass(frozen=True, slots=True)
class BacktestResult:
    metrics: BacktestMetrics
    fills: tuple[Fill, ...]
    equity_curve: tuple[float, ...]
    started_at: datetime
    ended_at: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "metrics": asdict(self.metrics),
            "fills": [asdict(fill) for fill in self.fills],
            "equity_curve": list(self.equity_curve),
        }

    def write_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def write_trades_csv(self, path: str | Path) -> None:
        columns = [
            "symbol", "side", "quantity", "entry_price", "exit_price",
            "gross_pnl", "costs", "net_pnl", "exit_reason",
        ]
        with Path(path).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            for fill in self.fills:
                row = asdict(fill)
                row["side"] = fill.side.value
                writer.writerow(row)


class Backtester:
    def __init__(self, config: BotConfig) -> None:
        self.config = config

    def run(self, bars: Iterable[Bar], *, close_open_position: bool = True) -> BacktestResult:
        ordered = sorted(bars, key=lambda bar: (bar.timestamp, bar.symbol))
        if not ordered:
            raise ValueError("backtest requires at least one bar")
        self._validate(ordered)
        engine = PaperTradingEngine(self.config)
        equity_curve = [self.config.initial_balance]
        latest_close: dict[str, float] = {}
        recorded_fills = 0
        for bar in ordered:
            latest_close[bar.symbol] = bar.close
            engine.on_bar(bar)
            if len(engine.broker.fills) > recorded_fills:
                equity_curve.append(engine.broker.balance)
                recorded_fills = len(engine.broker.fills)
        if close_open_position and engine.broker.position is not None:
            symbol = engine.broker.position.symbol
            fill = engine.broker.close_at_market(latest_close[symbol])
            if fill is not None:
                equity_curve.append(engine.broker.balance)
        fills = tuple(engine.broker.fills)
        return BacktestResult(
            metrics=calculate_metrics(self.config.initial_balance, fills, equity_curve),
            fills=fills,
            equity_curve=tuple(equity_curve),
            started_at=ordered[0].timestamp,
            ended_at=ordered[-1].timestamp,
        )

    def _validate(self, bars: list[Bar]) -> None:
        enabled = set(self.config.symbols)
        unknown = sorted({bar.symbol for bar in bars} - enabled)
        if unknown:
            raise ValueError(f"bars contain disabled symbols: {', '.join(unknown)}")
        seen: set[tuple[str, datetime]] = set()
        for bar in bars:
            key = (bar.symbol, bar.timestamp)
            if key in seen:
                raise ValueError(f"duplicate bar: {bar.symbol} at {bar.timestamp.isoformat()}")
            seen.add(key)


def calculate_metrics(
    initial_balance: float, fills: tuple[Fill, ...], equity_curve: list[float]
) -> BacktestMetrics:
    pnls = [fill.net_pnl for fill in fills]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    final_balance = equity_curve[-1]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    peak = equity_curve[0]
    max_drawdown = 0.0
    max_drawdown_fraction = 0.0
    for equity in equity_curve:
        peak = max(peak, equity)
        drawdown = peak - equity
        max_drawdown = max(max_drawdown, drawdown)
        max_drawdown_fraction = max(max_drawdown_fraction, drawdown / peak if peak else 0.0)
    average_win = mean(wins) if wins else 0.0
    average_loss = abs(mean(losses)) if losses else 0.0
    deviation = pstdev(pnls) if len(pnls) > 1 else 0.0
    return BacktestMetrics(
        initial_balance=initial_balance,
        final_balance=final_balance,
        net_profit=final_balance - initial_balance,
        return_fraction=(final_balance - initial_balance) / initial_balance,
        total_trades=len(pnls),
        winning_trades=len(wins),
        losing_trades=len(losses),
        win_rate=len(wins) / len(pnls) if pnls else 0.0,
        profit_factor=gross_profit / gross_loss if gross_loss else None,
        average_trade=mean(pnls) if pnls else 0.0,
        max_drawdown=max_drawdown,
        max_drawdown_fraction=max_drawdown_fraction,
        payoff_ratio=average_win / average_loss if average_loss else None,
        trade_sharpe=(mean(pnls) / deviation) * sqrt(len(pnls)) if deviation else None,
    )
