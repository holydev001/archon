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

