"""Renders Envoy bootstrap config dict to YAML string or file."""

import sys
from pathlib import Path
from typing import Union

import yaml

from envoy_local.builder import build_bootstrap
from envoy_local.config import EnvoyConfig


def render_yaml(cfg: EnvoyConfig) -> str:
    """Return the Envoy bootstrap config as a YAML string."""
    bootstrap = build_bootstrap(cfg)
    return yaml.dump(bootstrap, default_flow_style=False, sort_keys=False)


def write_yaml(cfg: EnvoyConfig, output: Union[str, Path, None] = None) -> Path:
    """Write the Envoy bootstrap YAML to a file.

    If *output* is None, writes to ``envoy-bootstrap.yaml`` in the current
    working directory.  Returns the path that was written.
    """
    if output is None:
        output = Path.cwd() / "envoy-bootstrap.yaml"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    content = render_yaml(cfg)
    output.write_text(content, encoding="utf-8")
    return output


def print_yaml(cfg: EnvoyConfig) -> None:
    """Print the rendered YAML to stdout."""
    sys.stdout.write(render_yaml(cfg))
