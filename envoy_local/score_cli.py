"""CLI entry-point for config scoring."""
from __future__ import annotations

import argparse
import sys

from envoy_local.loader import load_config
from envoy_local.scorer import score_config


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envoy-score",
        description="Score an Envoy local config file on best-practice dimensions.",
    )
    p.add_argument("config", help="Path to YAML/JSON config file")
    p.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        metavar="PCT",
        help="Exit non-zero if percentage score is below this threshold (0-100)",
    )
    p.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only print the final score line",
    )
    return p


def _validate_min_score(parser: argparse.ArgumentParser, value: float) -> None:
    """Validate that --min-score is within the acceptable 0-100 range."""
    if not (0.0 <= value <= 100.0):
        parser.error(f"--min-score must be between 0 and 100, got {value}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    _validate_min_score(parser, args.min_score)

    try:
        cfg = load_config(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR loading config: {exc}", file=sys.stderr)
        return 1

    result = score_config(cfg.listeners)

    if args.quiet:
        print(f"{result.total}/{result.max_total} ({result.percentage}%)")
    else:
        print(result.summary())

    if result.percentage < args.min_score:
        print(
            f"\nFAIL: score {result.percentage}% is below threshold {args.min_score}%",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
