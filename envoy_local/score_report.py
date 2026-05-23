"""Persist and print score reports."""
from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional

from envoy_local.scorer import ScoreResult

_REPORT_PREFIX = "score_report"


def _report_filename(directory: Path, label: Optional[str] = None) -> Path:
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    stem = f"{_REPORT_PREFIX}_{label}_{ts}" if label else f"{_REPORT_PREFIX}_{ts}"
    return directory / f"{stem}.txt"


def save_score_report(
    result: ScoreResult,
    directory: Path,
    label: Optional[str] = None,
) -> Path:
    """Write a human-readable score report to *directory* and return the path."""
    directory.mkdir(parents=True, exist_ok=True)
    path = _report_filename(directory, label)
    lines = [
        "=" * 60,
        "Envoy Local — Config Score Report",
        f"Generated: {datetime.datetime.utcnow().isoformat()} UTC",
    ]
    if label:
        lines.append(f"Label: {label}")
    lines += ["=" * 60, "", result.summary(), ""]
    path.write_text("\n".join(lines))
    return path


def print_score_report(result: ScoreResult, label: Optional[str] = None) -> None:
    """Print the score report to stdout."""
    if label:
        print(f"=== Score Report: {label} ===")
    print(result.summary())
