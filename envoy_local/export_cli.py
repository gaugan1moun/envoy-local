"""CLI entry-point for the envoy-local export command."""

from __future__ import annotations

import argparse
import sys

from envoy_local.loader import load_config
from envoy_local.builder import build_bootstrap
from envoy_local.validator import validate_config
from envoy_local.exporter import export_to_file, export_to_directory, ExportError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy-export",
        description="Export an envoy-local config to one or more YAML files.",
    )
    parser.add_argument(
        "input",
        help="Path to the input config file (YAML or JSON).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="envoy_out/bootstrap.yaml",
        help="Output file path (default: envoy_out/bootstrap.yaml).",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Fail if the output file already exists.",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip config validation before exporting.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.input)
    except Exception as exc:  # noqa: BLE001
        print(f"[error] Failed to load config: {exc}", file=sys.stderr)
        return 1

    if not args.skip_validation:
        errors = validate_config(cfg)
        if errors:
            print("[error] Validation failed:", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 1

    bootstrap = build_bootstrap(cfg)

    try:
        result = export_to_file(
            bootstrap,
            args.output,
            overwrite=not args.no_overwrite,
        )
    except ExportError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(result.summary())

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
