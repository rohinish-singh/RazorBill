"""CLI for offline CP1 dataset validation, splitting, and event evaluation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog import load_manifest, make_split_plan, report_markdown, validate_manifest
from .evaluation import evaluate_events


def _write_json(path: str, value: object) -> None:
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m datasets_incident_detection")
    subcommands = parser.add_subparsers(dest="command", required=True)
    validate = subcommands.add_parser("validate")
    validate.add_argument("manifest")
    validate.add_argument("--check-files", action="store_true")
    validate.add_argument("--json-report", required=True)
    validate.add_argument("--markdown-report")
    split = subcommands.add_parser("split")
    split.add_argument("manifest")
    split.add_argument("--seed", type=int, default=20261015)
    split.add_argument("--output", required=True)
    evaluate = subcommands.add_parser("evaluate")
    evaluate.add_argument("ground_truth")
    evaluate.add_argument("--predictions")
    evaluate.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "validate":
        manifest = load_manifest(args.manifest)
        report = validate_manifest(manifest, args.manifest, args.check_files)
        _write_json(args.json_report, report)
        if args.markdown_report:
            Path(args.markdown_report).write_text(report_markdown(report), encoding="utf-8")
        return 0 if report["valid"] else 1
    if args.command == "split":
        _write_json(args.output, make_split_plan(load_manifest(args.manifest), args.seed))
        return 0
    truth = json.loads(Path(args.ground_truth).read_text(encoding="utf-8"))
    predictions = json.loads(Path(args.predictions).read_text(encoding="utf-8")) if args.predictions else None
    _write_json(args.output, evaluate_events(truth, predictions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
