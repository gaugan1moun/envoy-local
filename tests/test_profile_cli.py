"""Tests for envoy_local.profile_cli."""

import textwrap
from pathlib import Path

import pytest
import yaml

from envoy_local.profile_cli import build_parser, main


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    data = {
        "clusters": [
            {
                "name": "backend",
                "hosts": [{"address": "127.0.0.1", "port": 8080}],
                "lb_policy": "round_robin",
            }
        ],
        "routes": [
            {"name": "default", "prefix": "/", "cluster": "backend"}
        ],
        "listeners": [
            {"name": "main", "address": "0.0.0.0", "port": 10000}
        ],
    }
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(data))
    return p


@pytest.fixture()
def no_listener_file(tmp_path: Path) -> Path:
    data = {
        "clusters": [
            {
                "name": "svc",
                "hosts": [{"address": "127.0.0.1", "port": 9000}],
            }
        ],
        "routes": [],
        "listeners": [],
    }
    p = tmp_path / "no_listener.yaml"
    p.write_text(yaml.dump(data))
    return p


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None


def test_main_returns_zero_for_valid_config(config_file):
    assert main([str(config_file)]) == 0


def test_main_returns_nonzero_for_warnings(no_listener_file):
    assert main([str(no_listener_file)]) != 0


def test_main_warn_only_flag_returns_zero(no_listener_file):
    assert main([str(no_listener_file), "--warn-only"]) == 0


def test_main_missing_file_returns_2(tmp_path):
    assert main([str(tmp_path / "nonexistent.yaml")]) == 2


def test_main_prints_summary(config_file, capsys):
    main([str(config_file)])
    captured = capsys.readouterr()
    assert "Clusters" in captured.out
    assert "Listeners" in captured.out
