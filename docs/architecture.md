# Architecture

Archon separates decisions from infrastructure so strategy research, simulation, MT5 integration,
and a future frontend can evolve independently.

```text
market data -> completed bars -> strategy -> signal -> risk gate -> broker adapter
                                      |           |             |
                                      +------ structured events +--> audit/frontend
```

## Boundaries

- `domain.py`: immutable market, signal, and order types.
- `strategy.py`: deterministic research baseline operating on completed bars.
- `risk.py`: mandatory approval gate and sizing policy.
- `simulation.py`: conservative paper fills with explicit costs.
- `engine.py`: orchestration and structured engine events.
- `brokers/`: external platform adapters; MT5 execution is intentionally absent.

Learning artifacts will be produced offline, versioned, and validated on unseen data. A candidate
cannot rewrite or promote itself while the trading process is running.
