import csv
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path


def write_synthetic_csv(
    path: str | Path,
    *,
    symbols: tuple[str, ...] = ("EURUSD", "GBPUSD"),
    bars_per_symbol: int = 500,
    seed: int = 42,
) -> None:
    """Create deterministic engineering data; never use it as evidence of profitability."""
    if bars_per_symbol < 2:
        raise ValueError("bars_per_symbol must be at least 2")
    rng = random.Random(seed)
    prices = {symbol: 1.1 + index * 0.15 for index, symbol in enumerate(symbols)}
    start = datetime(2026, 1, 1, tzinfo=UTC)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["symbol", "timestamp", "open", "high", "low", "close", "spread"],
        )
        writer.writeheader()
        for index in range(bars_per_symbol):
            regime_drift = 0.000015 if (index // 100) % 2 == 0 else -0.000015
            timestamp = start + timedelta(minutes=index)
            for symbol in symbols:
                open_price = prices[symbol]
                close = max(0.0001, open_price + regime_drift + rng.gauss(0, 0.00018))
                wick = abs(rng.gauss(0.00008, 0.00003))
                writer.writerow(
                    {
                        "symbol": symbol,
                        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
                        "open": f"{open_price:.6f}",
                        "high": f"{max(open_price, close) + wick:.6f}",
                        "low": f"{min(open_price, close) - wick:.6f}",
                        "close": f"{close:.6f}",
                        "spread": "0.000100",
                    }
                )
                prices[symbol] = close
