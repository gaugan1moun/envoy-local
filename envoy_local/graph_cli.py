"""CLI entry point for the config graph command."""
import argparse
import sys

from envoy_local.loader import load_config
from envoy_local.graph import build_graph


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy-graph",
        description="Display a dependency graph of an Envoy local config.",
    )
    parser.add_argument("config", help="Path to the YAML/JSON config file.")
    parser.add_argument(
        "--orphans-only",
        action="store_true",
        default=False,
        help="Only report orphaned (unreferenced) clusters.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"error: file not found: {args.config}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    graph = build_graph(config)

    if args.orphans_only:
        orphans = graph.orphaned_clusters()
        if orphans:
            print("Orphaned clusters:")
            for o in orphans:
                print(f"  - {o}")
            return 1
        print("No orphaned clusters.")
        return 0

    print(graph.as_text())
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
