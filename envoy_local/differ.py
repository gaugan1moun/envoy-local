"""Diff utility for comparing Envoy bootstrap configs across snapshots."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import List, Optional

import yaml


@dataclass
class DiffResult:
    """Result of comparing two YAML config strings."""

    old_label: str
    new_label: str
    lines: List[str]
    has_changes: bool

    def as_text(self) -> str:
        return "".join(self.lines)

    def summary(self) -> str:
        added = sum(1 for l in self.lines if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in self.lines if l.startswith("-") and not l.startswith("---"))
        if not self.has_changes:
            return "No differences found."
        return f"{added} line(s) added, {removed} line(s) removed."


def _normalise_yaml(raw: str) -> List[str]:
    """Round-trip through PyYAML to normalise formatting before diffing."""
    parsed = yaml.safe_load(raw)
    normalised = yaml.dump(parsed, default_flow_style=False, sort_keys=True)
    return normalised.splitlines(keepends=True)


def diff_configs(
    old_yaml: str,
    new_yaml: str,
    old_label: str = "old",
    new_label: str = "new",
    context_lines: int = 3,
) -> DiffResult:
    """Return a unified diff between two YAML config strings."""
    old_lines = _normalise_yaml(old_yaml)
    new_lines = _normalise_yaml(new_yaml)

    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=old_label,
            tofile=new_label,
            n=context_lines,
        )
    )
    return DiffResult(
        old_label=old_label,
        new_label=new_label,
        lines=diff_lines,
        has_changes=bool(diff_lines),
    )


def diff_snapshots(
    old_yaml: str,
    new_yaml: str,
    old_name: str = "snapshot-old",
    new_name: str = "snapshot-new",
) -> DiffResult:
    """Convenience wrapper for diffing two named snapshots."""
    return diff_configs(old_yaml, new_yaml, old_label=old_name, new_label=new_name)
