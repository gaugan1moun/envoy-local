"""High-level pipeline: load → validate → build → render."""

import logging
from pathlib import Path
from typing import Optional

from envoy_local.loader import load_config
from envoy_local.validator import validate_config
from envoy_local.builder import build_bootstrap
from envoy_local.renderer import write_yaml, print_yaml

logger = logging.getLogger(__name__)


def run_pipeline(
    source: Path,
    output: Optional[Path] = None,
    *,
    strict: bool = True,
) -> str:
    """Load *source*, validate, build bootstrap, and render to YAML string.

    If *output* is given the YAML is also written to that file.
    Raises ``ValidationError`` when *strict* is True (default).
    Returns the rendered YAML string.
    """
    logger.debug("Loading config from %s", source)
    config = load_config(source)

    clusters = config["clusters"]
    listeners = config["listeners"]

    if strict:
        logger.debug("Validating config")
        errors = validate_config(clusters=clusters, listeners=listeners)
        if errors:
            from envoy_local.validator import ValidationError
            raise ValidationError("\n".join(str(e) for e in errors))

    logger.debug("Building bootstrap")
    bootstrap = build_bootstrap(clusters=clusters, listeners=listeners)

    if output:
        logger.info("Writing rendered config to %s", output)
        write_yaml(bootstrap, output)
    else:
        print_yaml(bootstrap)

    from envoy_local.renderer import render_yaml
    return render_yaml(bootstrap)
