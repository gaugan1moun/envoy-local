"""CLI entry-point for the template preset feature."""

import argparse
import json
import sys
from typing import List, Optional

from envoy_local.template import apply_preset, list_presets, TemplateError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy-template",
        description="Apply a named config preset and print the resulting overrides.",
    )
    sub = parser.add_subparsers(dest="command")

    # list sub-command
    sub.add_parser("list", help="List available presets")

    # apply sub-command
    apply_p = sub.add_parser("apply", help="Apply a preset and show overrides")
    apply_p.add_argument("preset", help="Preset name (e.g. http_default)")
    apply_p.add_argument(
        "--override",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        help="Override a preset key, e.g. --override max_retries=5",
    )
    apply_p.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )

    return parser


def _parse_overrides(raw: List[str]) -> dict:
    result = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"Override must be KEY=VALUE, got: {item!r}")
        k, v = item.split("=", 1)
        result[k.strip()] = v.strip()
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        for name in list_presets():
            print(f"  {name}")
        return 0

    if args.command == "apply":
        try:
            overrides = _parse_overrides(args.override)
            result = apply_preset(args.preset, overrides or None)
        except (TemplateError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        if args.format == "json":
            print(json.dumps(result.as_dict(), indent=2))
        else:
            print(f"Preset : {result.preset_name}")
            print(f"Cluster: {result.cluster_overrides}")
            print(f"Route  : {result.route_overrides}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
