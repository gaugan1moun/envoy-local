"""High-level pipeline: load → validate → render → (optionally snapshot)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envoy_local.builder import build_bootstrap
from envoy_local.loader import load_config
from envoy_local.renderer import render_yaml, write_yaml
from envoy_local.snapshotter import DEFAULT_SNAPSHOT_DIR, save_snapshot
from envoy_local.validator import validate_config


def run_pipeline(
    input_path: str,
    output_path: Optional[str] = None,
    snapshot_name: Optional[str] = None,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    print_output: bool = False,
) -> str:
    """
    Execute the full config pipeline.

    1. Load config from *input_path* (YAML or JSON).
    2. Validate all clusters, routes, and listeners.
    3. Build the Envoy bootstrap structure.
    4. Render to YAML.
    5. Optionally write to *output_path*.
    6. Optionally save a named snapshot.

    Returns the rendered YAML string.
    """
    config = load_config(input_path)

    errors = validate_config(config)
    if errors:
        messages = "\n".join(f"  - {e}" for e in errors)
        raise ValueError(f"Config validation failed:\n{messages}")

    bootstrap = build_bootstrap(config)
    yaml_str = render_yaml(bootstrap)

    if print_output:
        print(yaml_str)

    if output_path:
        write_yaml(bootstrap, output_path)

    if snapshot_name:
        save_snapshot(
            snapshot_name,
            yaml_str,
            directory=snapshot_dir,
            metadata={"source": input_path},
        )

    return yaml_str
