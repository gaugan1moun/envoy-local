"""Tests for envoy_local.differ."""

from __future__ import annotations

import pytest

from envoy_local.differ import DiffResult, diff_configs, diff_snapshots

YAML_A = """\
static_resources:
  clusters:
    - name: service_a
      connect_timeout: 0.25s
"""

YAML_B = """\
static_resources:
  clusters:
    - name: service_b
      connect_timeout: 0.25s
"""

YAML_A2 = """\
static_resources:
  clusters:
    - connect_timeout: 0.25s
      name: service_a
"""


def test_diff_detects_changes():
    result = diff_configs(YAML_A, YAML_B)
    assert result.has_changes is True


def test_diff_no_changes_identical():
    result = diff_configs(YAML_A, YAML_A)
    assert result.has_changes is False


def test_diff_no_changes_after_normalisation():
    """Key ordering differences should not count as changes after YAML round-trip."""
    result = diff_configs(YAML_A, YAML_A2)
    assert result.has_changes is False


def test_diff_labels_propagated():
    result = diff_configs(YAML_A, YAML_B, old_label="v1", new_label="v2")
    assert result.old_label == "v1"
    assert result.new_label == "v2"


def test_diff_lines_contain_changed_content():
    result = diff_configs(YAML_A, YAML_B)
    text = result.as_text()
    assert "service_a" in text or "service_b" in text


def test_summary_no_changes():
    result = diff_configs(YAML_A, YAML_A)
    assert "No differences" in result.summary()


def test_summary_with_changes():
    result = diff_configs(YAML_A, YAML_B)
    summary = result.summary()
    assert "added" in summary
    assert "removed" in summary


def test_diff_snapshots_is_alias():
    result = diff_snapshots(YAML_A, YAML_B, old_name="snap-1", new_name="snap-2")
    assert isinstance(result, DiffResult)
    assert result.old_label == "snap-1"
    assert result.new_label == "snap-2"


def test_context_lines_respected():
    result_wide = diff_configs(YAML_A, YAML_B, context_lines=10)
    result_narrow = diff_configs(YAML_A, YAML_B, context_lines=0)
    assert len(result_wide.lines) >= len(result_narrow.lines)
