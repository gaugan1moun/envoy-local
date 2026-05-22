"""Tests for envoy_local.snapshotter."""

import pytest
from pathlib import Path

from envoy_local.snapshotter import (
    SnapshotError,
    delete_snapshot,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)

SAMPLE_YAML = "static_resources:\n  clusters: []\n"


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path / "snapshots"


def test_save_creates_file(snap_dir):
    path = save_snapshot("v1", SAMPLE_YAML, directory=snap_dir)
    assert path.exists()
    assert path.name == "v1.json"


def test_load_returns_yaml(snap_dir):
    save_snapshot("v1", SAMPLE_YAML, directory=snap_dir)
    result = load_snapshot("v1", directory=snap_dir)
    assert result == SAMPLE_YAML


def test_load_missing_raises(snap_dir):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot("ghost", directory=snap_dir)


def test_save_with_metadata(snap_dir):
    save_snapshot("v2", SAMPLE_YAML, directory=snap_dir, metadata={"env": "staging"})
    entries = list_snapshots(directory=snap_dir)
    assert entries[0]["metadata"]["env"] == "staging"


def test_list_empty_when_no_dir(snap_dir):
    result = list_snapshots(directory=snap_dir)
    assert result == []


def test_list_returns_sorted_entries(snap_dir):
    save_snapshot("alpha", SAMPLE_YAML, directory=snap_dir)
    save_snapshot("beta", SAMPLE_YAML, directory=snap_dir)
    entries = list_snapshots(directory=snap_dir)
    assert len(entries) == 2
    names = [e["name"] for e in entries]
    assert "alpha" in names and "beta" in names


def test_list_contains_required_keys(snap_dir):
    save_snapshot("v1", SAMPLE_YAML, directory=snap_dir)
    entry = list_snapshots(directory=snap_dir)[0]
    assert "name" in entry
    assert "created_at" in entry
    assert "metadata" in entry


def test_delete_existing_snapshot(snap_dir):
    save_snapshot("v1", SAMPLE_YAML, directory=snap_dir)
    deleted = delete_snapshot("v1", directory=snap_dir)
    assert deleted is True
    assert not (snap_dir / "v1.json").exists()


def test_delete_missing_returns_false(snap_dir):
    result = delete_snapshot("nonexistent", directory=snap_dir)
    assert result is False


def test_overwrite_snapshot(snap_dir):
    save_snapshot("v1", SAMPLE_YAML, directory=snap_dir)
    new_yaml = "static_resources:\n  clusters: [{}]\n"
    save_snapshot("v1", new_yaml, directory=snap_dir)
    result = load_snapshot("v1", directory=snap_dir)
    assert result == new_yaml
