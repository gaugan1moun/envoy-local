"""Tests for envoy_local.diff_report."""

from __future__ import annotations

import pytest

from envoy_local.differ import diff_configs
from envoy_local.diff_report import print_diff_report, save_diff_report

YAML_A = "static_resources:\n  clusters:\n    - name: svc_a\n"
YAML_B = "static_resources:\n  clusters:\n    - name: svc_b\n"


@pytest.fixture()
def changed_result():
    return diff_configs(YAML_A, YAML_B, old_label="old", new_label="new")


@pytest.fixture()
def unchanged_result():
    return diff_configs(YAML_A, YAML_A, old_label="same", new_label="same")


def test_save_creates_file(tmp_path, changed_result):
    path = save_diff_report(changed_result, report_dir=tmp_path)
    assert path.exists()
    assert path.suffix == ".txt"


def test_save_file_contains_header(tmp_path, changed_result):
    path = save_diff_report(changed_result, report_dir=tmp_path)
    content = path.read_text()
    assert "Envoy Config Diff Report" in content
    assert "old" in content
    assert "new" in content


def test_save_file_contains_diff_body(tmp_path, changed_result):
    path = save_diff_report(changed_result, report_dir=tmp_path)
    content = path.read_text()
    assert "svc_a" in content or "svc_b" in content


def test_save_no_changes_still_creates_file(tmp_path, unchanged_result):
    path = save_diff_report(unchanged_result, report_dir=tmp_path)
    assert path.exists()
    content = path.read_text()
    assert "Envoy Config Diff Report" in content


def test_save_creates_report_dir_if_missing(tmp_path, changed_result):
    nested = tmp_path / "a" / "b" / "reports"
    save_diff_report(changed_result, report_dir=nested)
    assert nested.is_dir()


def test_print_diff_no_colour_no_exception(capsys, changed_result):
    print_diff_report(changed_result, colour=False)
    out = capsys.readouterr().out
    assert "Diff:" in out


def test_print_diff_unchanged_shows_summary(capsys, unchanged_result):
    print_diff_report(unchanged_result, colour=False)
    out = capsys.readouterr().out
    assert "No differences" in out


def test_print_diff_colour_no_exception(capsys, changed_result):
    print_diff_report(changed_result, colour=True)
    out = capsys.readouterr().out
    assert "Diff:" in out
