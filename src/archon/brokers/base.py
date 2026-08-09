from typing import Protocol

from archon.domain import Bar, OrderIntent


class MarketDataSource(Protocol):
    def latest_completed_bars(self, symbol: str, count: int) -> list[Bar]: ...


class DemoExecutionBroker(Protocol):
    def submit(self, order: OrderIntent) -> str: ...

    def close_all(self) -> None: ...

