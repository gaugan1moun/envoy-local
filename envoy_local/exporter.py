"""Export rendered Envoy configs to various output targets."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envoy_local.renderer import render_yaml


class ExportError(Exception):
    """Raised when an export operation fails."""


@dataclass
class ExportResult:
    destination: str
    bytes_written: int
    format: str = "yaml"
    metadata: dict = field(default_factory=dict)

    def summary(self) -> str:
        return (
            f"Exported {self.bytes_written} bytes ({self.format}) "
            f"-> {self.destination}"
        )


def export_to_file(
    bootstrap: dict,
    output_path: str,
    overwrite: bool = True,
    mkdir: bool = True,
) -> ExportResult:
    """Render bootstrap config and write it to *output_path*."""
    path = Path(output_path)

    if mkdir:
        path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and not overwrite:
        raise ExportError(
            f"Output file already exists and overwrite=False: {output_path}"
        )

    content = render_yaml(bootstrap)
    path.write_text(content, encoding="utf-8")

    return ExportResult(
        destination=str(path.resolve()),
        bytes_written=len(content.encode("utf-8")),
        format="yaml",
    )


def export_to_directory(
    configs: dict[str, dict],
    output_dir: str,
    overwrite: bool = True,
) -> list[ExportResult]:
    """Export multiple named bootstrap configs into *output_dir*.

    Args:
        configs: Mapping of filename stem -> bootstrap dict.
        output_dir: Target directory (created if absent).
        overwrite: Whether to overwrite existing files.

    Returns:
        List of ExportResult, one per file written.
    """
    results: list[ExportResult] = []
    for name, bootstrap in configs.items():
        filename = name if name.endswith(".yaml") else f"{name}.yaml"
        result = export_to_file(
            bootstrap,
            os.path.join(output_dir, filename),
            overwrite=overwrite,
            mkdir=True,
        )
        results.append(result)
    return results


def copy_export(
    source_path: str,
    dest_path: str,
    overwrite: bool = True,
) -> ExportResult:
    """Copy an already-rendered config file to a new destination."""
    src = Path(source_path)
    if not src.exists():
        raise ExportError(f"Source file not found: {source_path}")

    dst = Path(dest_path)
    if dst.exists() and not overwrite:
        raise ExportError(
            f"Destination already exists and overwrite=False: {dest_path}"
        )

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
    content = dst.read_bytes()

    return ExportResult(
        destination=str(dst.resolve()),
        bytes_written=len(content),
        format="yaml",
    )
