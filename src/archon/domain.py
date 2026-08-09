from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True, slots=True)
class Bar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    spread: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError("bar timestamp must be timezone-aware")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("prices must be positive")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("OHLC values are inconsistent")
        if self.spread < 0:
            raise ValueError("spread cannot be negative")


@dataclass(frozen=True, slots=True)
class Signal:
    symbol: str
    side: Side
    timestamp: datetime
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class OrderIntent:
    symbol: str
    side: Side
    quantity: float
    entry_price: float
    stop_loss: float
    take_profit: float
    created_at: datetime

    @property
    def risk_per_unit(self) -> float:
        return abs(self.entry_price - self.stop_loss)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

