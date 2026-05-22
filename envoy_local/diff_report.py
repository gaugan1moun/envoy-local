"""Render and persist diff reports for Envoy config comparisons."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from envoy_local.differ import DiffResult


DEFAULT_REPORT_DIR = Path(".envoy_diff_reports")


def _report_filename(old_label: str, new_label: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_old = old_label.replace("/", "_").replace(" ", "_")
    safe_new = new_label.replace("/", "_").replace(" ", "_")
    return f"diff_{safe_old}_vs_{safe_new}_{ts}.txt"


def save_diff_report(
    result: DiffResult,
    report_dir: Path = DEFAULT_REPORT_DIR,
) -> Path:
    """Write a diff report to *report_dir* and return the file path."""
    report_dir.mkdir(parents=True, exist_ok=True)
    filename = _report_filename(result.old_label, result.new_label)
    out_path = report_dir / filename

    header = (
        f"# Envoy Config Diff Report\n"
        f"# From : {result.old_label}\n"
        f"# To   : {result.new_label}\n"
        f"# Summary: {result.summary()}\n"
        f"# Generated: {datetime.now(timezone.utc).isoformat()}\n"
        f"{'#' * 60}\n"
    )
    out_path.write_text(header + result.as_text(), encoding="utf-8")
    return out_path


def print_diff_report(result: DiffResult, *, colour: bool = True) -> None:
    """Print a diff result to stdout with optional ANSI colouring."""
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    CYAN = "\033[36m"

    print(f"Diff: {result.old_label} → {result.new_label}")
    print(result.summary())
    if not result.has_changes:
        return
    for line in result.lines:
        if not colour:
            print(line, end="")
        elif line.startswith("+"):
            print(f"{GREEN}{line}{RESET}", end="")
        elif line.startswith("-"):
            print(f"{RED}{line}{RESET}", end="")
        elif line.startswith("@@"):
            print(f"{CYAN}{line}{RESET}", end="")
        else:
            print(line, end="")
