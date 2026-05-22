"""CLI entry-point for the envoy-local linter."""

import argparse
import sys

from envoy_local.loader import load_config
from envoy_local.linter import lint_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy-lint",
        description="Lint an envoy-local YAML/JSON config for common issues.",
    )
    parser.add_argument("config", help="Path to the config file (YAML or JSON).")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any warnings are present (not just errors).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-issue output; only print the summary line.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Failed to load config: {exc}", file=sys.stderr)
        return 2

    result = lint_config(cfg.listeners, cfg.clusters)

    if not args.quiet:
        for warning in result.warnings:
            print(warning)

    print(f"Lint complete: {result.summary()}")

    if result.has_errors:
        return 1
    if args.strict and result.has_warnings:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
