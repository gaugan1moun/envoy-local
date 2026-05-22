"""Tests for envoy_local.watcher."""

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from envoy_local.watcher import ConfigWatcher, _file_hash


@pytest.fixture()
def config_file(tmp_path):
    p = tmp_path / "envoy.yaml"
    p.write_text("clusters: []")
    return p


def test_file_hash_is_stable(config_file):
    h1 = _file_hash(config_file)
    h2 = _file_hash(config_file)
    assert h1 == h2


def test_file_hash_changes_on_write(config_file):
    h1 = _file_hash(config_file)
    config_file.write_text("clusters: [{}]")
    h2 = _file_hash(config_file)
    assert h1 != h2


def test_check_once_no_callback_on_first_call(config_file):
    cb = MagicMock()
    watcher = ConfigWatcher(config_file, cb)
    changed = watcher.check_once()
    # First check seeds the hash — no callback yet.
    assert changed is True
    cb.assert_not_called()


def test_check_once_callback_on_change(config_file):
    cb = MagicMock()
    watcher = ConfigWatcher(config_file, cb)
    watcher.check_once()  # seed
    config_file.write_text("clusters: [{name: x}]")
    changed = watcher.check_once()
    assert changed is True
    cb.assert_called_once_with(config_file)


def test_check_once_no_callback_when_unchanged(config_file):
    cb = MagicMock()
    watcher = ConfigWatcher(config_file, cb)
    watcher.check_once()  # seed
    changed = watcher.check_once()  # same content
    assert changed is False
    cb.assert_not_called()


def test_missing_source_returns_false(tmp_path):
    cb = MagicMock()
    watcher = ConfigWatcher(tmp_path / "ghost.yaml", cb)
    assert watcher.check_once() is False
    cb.assert_not_called()


def test_stop_exits_loop(config_file):
    cb = MagicMock()
    watcher = ConfigWatcher(config_file, cb, poll_interval=0.05)

    import threading

    t = threading.Thread(target=watcher.start, daemon=True)
    t.start()
    time.sleep(0.15)
    watcher.stop()
    t.join(timeout=1.0)
    assert not t.is_alive()
