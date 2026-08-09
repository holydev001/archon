import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from archon.risk import RiskLimits
from archon.strategy import MovingAverageConfig


@dataclass(frozen=True, slots=True)
class BotConfig:
    symbols: tuple[str, ...] = ("EURUSD", "GBPUSD")
    initial_balance: float = 10_000.0
    stop_distance: float = 0.0010
    reward_risk_ratio: float = 1.5
    slippage: float = 0.00002
    commission_per_unit: float = 0.0
    strategy: MovingAverageConfig = field(default_factory=MovingAverageConfig)
    risk: RiskLimits = field(default_factory=RiskLimits)


def load_config(path: str | Path) -> BotConfig:
    with Path(path).open("rb") as handle:
        raw = tomllib.load(handle)
    strategy = MovingAverageConfig(**raw.get("strategy", {}))
    risk = RiskLimits(**raw.get("risk", {}))
    root = {key: value for key, value in raw.items() if key not in {"strategy", "risk"}}
    if "symbols" in root:
        root["symbols"] = tuple(root["symbols"])
    return BotConfig(strategy=strategy, risk=risk, **root)

