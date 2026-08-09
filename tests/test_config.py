from archon.config import load_config


def test_loads_example_config() -> None:
    config = load_config("config.example.toml")
    assert config.symbols == ("EURUSD", "GBPUSD")
    assert config.strategy.fast_window == 5
    assert config.risk.max_open_positions == 1

