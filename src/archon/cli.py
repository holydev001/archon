import argparse
import csv
import json
from datetime import datetime

from archon.config import load_config
from archon.domain import Bar
from archon.engine import PaperTradingEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Archon demo-first Forex scalper")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="check the local runtime")
    run = subparsers.add_parser("run-csv", help="paper trade completed bars from a CSV file")
    run.add_argument("csv_file")
    run.add_argument("--config", default="config.example.toml")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        print("Archon runtime: OK")
    elif args.command == "run-csv":
        engine = PaperTradingEngine(load_config(args.config))
        with open(args.csv_file, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                bar = Bar(
                    symbol=row["symbol"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    spread=float(row.get("spread", 0.0)),
                )
                for event in engine.on_bar(bar):
                    print(json.dumps({"time": row["timestamp"], "kind": event.kind, "message": event.message}))
        print(json.dumps({"balance": engine.broker.balance, "closed_trades": len(engine.broker.fills)}))
    return 0
