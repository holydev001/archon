from datetime import UTC, datetime

from archon.domain import Bar


class MT5Unavailable(RuntimeError):
    pass


class MT5MarketData:
    """Thin, read-only MT5 adapter. Execution stays disabled until separately implemented."""

    def __init__(self, timeframe: int | None = None) -> None:
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise MT5Unavailable('install the optional dependency with: pip install -e ".[mt5]"') from exc
        self._mt5 = mt5
        self._timeframe = timeframe if timeframe is not None else mt5.TIMEFRAME_M1

    def connect(self) -> None:
        if not self._mt5.initialize():
            raise MT5Unavailable(f"MT5 initialize failed: {self._mt5.last_error()}")

    def latest_completed_bars(self, symbol: str, count: int) -> list[Bar]:
        # Start at position 1 so the still-forming candle is never used for a decision.
        rates = self._mt5.copy_rates_from_pos(symbol, self._timeframe, 1, count)
        if rates is None:
            raise MT5Unavailable(f"MT5 data request failed: {self._mt5.last_error()}")
        return [
            Bar(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(int(rate["time"]), UTC),
                open=float(rate["open"]),
                high=float(rate["high"]),
                low=float(rate["low"]),
                close=float(rate["close"]),
                spread=float(rate["spread"]) * float(self._mt5.symbol_info(symbol).point),
            )
            for rate in rates
        ]

    def close(self) -> None:
        self._mt5.shutdown()
