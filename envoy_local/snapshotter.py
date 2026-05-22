"""Snapshot management: save and load named config snapshots to disk."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_SNAPSHOT_DIR = Path(".envoy_snapshots")


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshot_path(name: str, directory: Path) -> Path:
    return directory / f"{name}.json"


def save_snapshot(
    name: str,
    yaml_content: str,
    directory: Path = DEFAULT_SNAPSHOT_DIR,
    metadata: Optional[Dict] = None,
) -> Path:
    """Persist a rendered YAML config as a named snapshot."""
    directory.mkdir(parents=True, exist_ok=True)
    path = _snapshot_path(name, directory)
    payload = {
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "yaml": yaml_content,
        "metadata": metadata or {},
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def load_snapshot(name: str, directory: Path = DEFAULT_SNAPSHOT_DIR) -> str:
    """Return the YAML string stored in a named snapshot."""
    path = _snapshot_path(name, directory)
    if not path.exists():
        raise SnapshotError(f"Snapshot '{name}' not found in {directory}")
    payload = json.loads(path.read_text())
    return payload["yaml"]


def list_snapshots(directory: Path = DEFAULT_SNAPSHOT_DIR) -> List[Dict]:
    """Return metadata for all snapshots in the directory, sorted by creation time."""
    if not directory.exists():
        return []
    entries = []
    for p in directory.glob("*.json"):
        try:
            payload = json.loads(p.read_text())
            entries.append({
                "name": payload["name"],
                "created_at": payload["created_at"],
                "metadata": payload.get("metadata", {}),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return sorted(entries, key=lambda e: e["created_at"])


def delete_snapshot(name: str, directory: Path = DEFAULT_SNAPSHOT_DIR) -> bool:
    """Delete a named snapshot. Returns True if deleted, False if not found."""
    path = _snapshot_path(name, directory)
    if not path.exists():
        return False
    path.unlink()
    return True
