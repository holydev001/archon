# Archon Scalper

Archon is a demo-first Forex scalping research bot. The first milestone is deliberately
small: deterministic signals, hard risk limits, reproducible paper trading, and complete
decision logs. Live trading and self-modifying production code are out of scope.

## Safety model

- Demo or offline paper trading only.
- No martingale, averaging down, or live self-modification.
- Every proposed order passes through a central risk gate.
- Strategy candidates must be tested on unseen data and include spread/slippage costs.
- Broker credentials must never be committed to this repository.

## Development

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
python -m archon --help
```

The domain and simulation layers do not import MetaTrader 5. A future adapter will translate
between MT5 data/orders and these stable interfaces, which also leaves room for a frontend.

## Current milestone

The feature branch includes:

- validated OHLC bar, signal, and order models;
- a moving-average crossover baseline (a testable benchmark, not a profit claim);
- position sizing plus per-trade, spread, daily-loss, drawdown, and exposure limits;
- conservative paper fills with slippage and commission;
- a read-only MT5 completed-candle adapter; and
- a CSV paper-trading CLI that emits JSON events suitable for a future frontend.

CSV input requires `symbol,timestamp,open,high,low,close` columns and accepts an optional
`spread` column. Timestamps must include a UTC offset, for example `2026-08-09T12:00:00Z`.

```powershell
python -m archon run-csv .\data\bars.csv --config .\config.example.toml
```

MT5 order execution is intentionally not implemented yet. Connecting the demo account comes
after the broker, terminal installation, symbol names, and contract sizing have been confirmed.
