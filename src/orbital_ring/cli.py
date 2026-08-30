"""Command-line interface for scenario runs, sweeps, and reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from orbital_ring.analysis import evaluate_scenario
from orbital_ring.config import load_scenario
from orbital_ring.evidence import generate_hardening_evidence
from orbital_ring.or2_evidence import generate_or2_evidence
from orbital_ring.report import generate_baseline_report
from orbital_ring.sweep import run_sweep


def _write_simulation(result, output_directory: Path) -> Path:
    output_directory.mkdir(parents=True, exist_ok=True)
    result_path = output_directory / "result.json"
    payload = result.to_dict()
    result_path.write_text(
        json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8"
    )
    (output_directory / "manifest.json").write_text(
        json.dumps(payload["manifest"], indent=2, allow_nan=False), encoding="utf-8"
    )
    return result_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orbital-ring", description="Traceable OR-0 / OR-1 simulation kernel"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="evaluate one YAML scenario")
    run_parser.add_argument("scenario", type=Path)
    run_parser.add_argument("--output", type=Path, required=True)

    sweep_parser = subparsers.add_parser("sweep", help="run an explicit sweep configuration")
    sweep_parser.add_argument("configuration", type=Path)
    sweep_parser.add_argument("--output", type=Path, required=True)
    sweep_parser.add_argument(
        "--allow-cartesian",
        action="store_true",
        help="authorize a configured Cartesian product after reviewing its size",
    )

    report_parser = subparsers.add_parser("report", help="generate baseline Markdown and plots")
    report_parser.add_argument("scenario", type=Path)
    report_parser.add_argument("--output", type=Path, required=True)

    evidence_parser = subparsers.add_parser(
        "evidence", help="generate OR-1.1 validation and design-space tables"
    )
    evidence_parser.add_argument("scenario", type=Path)
    evidence_parser.add_argument("--output", type=Path, required=True)

    or2_parser = subparsers.add_parser(
        "or2-evidence", help="generate OR-2 M0/M1 magnetic feasibility evidence"
    )
    or2_parser.add_argument("scenario", type=Path)
    or2_parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        result = evaluate_scenario(load_scenario(args.scenario))
        path = _write_simulation(result, args.output)
        print(path)
        return 0
    if args.command == "sweep":
        frame = run_sweep(
            args.configuration,
            args.output,
            allow_cartesian=args.allow_cartesian,
        )
        print(f"wrote {len(frame)} design points to {args.output}")
        return 0
    if args.command == "report":
        path = generate_baseline_report(args.scenario, args.output)
        print(path)
        return 0
    if args.command == "evidence":
        path = generate_hardening_evidence(args.scenario, args.output)
        print(path)
        return 0
    if args.command == "or2-evidence":
        path = generate_or2_evidence(args.scenario, args.output)
        print(path)
        return 0
    raise AssertionError(f"unhandled command {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
