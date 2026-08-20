import argparse
import json
from pathlib import Path

from archon.backtest import Backtester
from archon.config import load_config
from archon.datasets import chronological_split, load_bars_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Archon demo-first Forex scalper")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="check the local runtime")
    run = subparsers.add_parser("backtest", help="backtest completed bars from a CSV file")
    run.add_argument("csv_file")
    run.add_argument("--config", default="config.example.toml")
    run.add_argument("--output", default="artifacts/backtest")
    run.add_argument(
        "--train-fraction",
        type=float,
        help="chronologically split data and report train/test periods separately",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        print("Archon runtime: OK")
    elif args.command == "backtest":
        _run_backtest(args)
    return 0


def _run_backtest(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    bars = load_bars_csv(args.csv_file)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    periods = {"full": bars}
    if args.train_fraction is not None:
        train, test = chronological_split(bars, args.train_fraction)
        periods = {"train": train, "test": test}
    summary = {}
    for name, period_bars in periods.items():
        result = Backtester(config).run(period_bars)
        result.write_json(output / f"{name}.json")
        result.write_trades_csv(output / f"{name}-trades.csv")
        summary[name] = result.to_dict()["metrics"]
    print(json.dumps(summary, indent=2))
