"""CLI entry point for profiling an Envoy local config file."""

import argparse
import sys

from envoy_local.loader import load_config
from envoy_local.profiler import profile_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy-profile",
        description="Profile an envoy-local config file and report complexity metrics.",
    )
    parser.add_argument("input", help="Path to YAML or JSON config file")
    parser.add_argument(
        "--warn-only",
        action="store_true",
        default=False,
        help="Exit 0 even when warnings are present",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.input)
    except FileNotFoundError:
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 2

    result = profile_config(config)
    print(result.summary())

    if result.warnings and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
