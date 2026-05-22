"""CLI entry-point for diffing two Envoy config snapshots."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy_local.differ import diff_snapshots
from envoy_local.diff_report import print_diff_report, save_diff_report
from envoy_local.snapshotter import load_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy-diff",
        description="Compare two Envoy config snapshots.",
    )
    parser.add_argument("old", help="Name of the older snapshot.")
    parser.add_argument("new", help="Name of the newer snapshot.")
    parser.add_argument(
        "--snapshot-dir",
        default=".envoy_snapshots",
        help="Directory containing snapshots (default: .envoy_snapshots).",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the diff report to disk.",
    )
    parser.add_argument(
        "--report-dir",
        default=".envoy_diff_reports",
        help="Directory to save diff reports (default: .envoy_diff_reports).",
    )
    parser.add_argument(
        "--no-colour",
        action="store_true",
        help="Disable ANSI colour output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    snap_dir = Path(args.snapshot_dir)

    try:
        old_yaml = load_snapshot(args.old, snapshot_dir=snap_dir)
        new_yaml = load_snapshot(args.new, snapshot_dir=snap_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 1

    result = diff_snapshots(old_yaml, new_yaml, old_name=args.old, new_name=args.new)
    print_diff_report(result, colour=not args.no_colour)

    if args.save:
        report_path = save_diff_report(result, report_dir=Path(args.report_dir))
        print(f"\nReport saved to: {report_path}")

    return 0 if not result.has_changes else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
