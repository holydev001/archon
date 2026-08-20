from archon.datasets import load_bars_csv
from archon.synthetic import write_synthetic_csv


def test_synthetic_data_is_deterministic_and_loadable(tmp_path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    write_synthetic_csv(first, bars_per_symbol=5, seed=7)
    write_synthetic_csv(second, bars_per_symbol=5, seed=7)
    assert first.read_bytes() == second.read_bytes()
    bars = load_bars_csv(first)
    assert len(bars) == 10
    assert {bar.symbol for bar in bars} == {"EURUSD", "GBPUSD"}
