from collections import deque
from dataclasses import dataclass

from archon.domain import Bar, Side, Signal


@dataclass(frozen=True, slots=True)
class MovingAverageConfig:
    fast_window: int = 5
    slow_window: int = 20
    min_separation_fraction: float = 0.00005

    def __post_init__(self) -> None:
        if self.fast_window < 2 or self.slow_window <= self.fast_window:
            raise ValueError("windows require 2 <= fast < slow")


class MovingAverageCrossStrategy:
    """Emits only on a completed-bar crossover, avoiding repeated same-direction signals."""

    def __init__(self, config: MovingAverageConfig) -> None:
        self.config = config
        self._closes: deque[float] = deque(maxlen=config.slow_window)
        self._previous_relation = 0

    def on_bar(self, bar: Bar) -> Signal | None:
        self._closes.append(bar.close)
        if len(self._closes) < self.config.slow_window:
            return None
        closes = list(self._closes)
        fast = sum(closes[-self.config.fast_window :]) / self.config.fast_window
        slow = sum(closes) / self.config.slow_window
        separation = (fast - slow) / slow
        relation = 1 if separation > 0 else -1 if separation < 0 else 0
        crossed = self._previous_relation != 0 and relation != self._previous_relation
        self._previous_relation = relation
        if not crossed or abs(separation) < self.config.min_separation_fraction:
            return None
        side = Side.BUY if relation > 0 else Side.SELL
        return Signal(
            symbol=bar.symbol,
            side=side,
            timestamp=bar.timestamp,
            confidence=min(1.0, abs(separation) / self.config.min_separation_fraction),
            reason=f"MA crossover: fast={fast:.6f}, slow={slow:.6f}",
        )

