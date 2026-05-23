"""Tests for envoy_local.score_cli."""
import json
import textwrap
from pathlib import Path

import pytest

from envoy_local.score_cli import build_parser, main


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    data = {
        "listeners": [
            {
                "name": "ingress",
                "port": 10000,
                "routes": [
                    {
                        "match_prefix": "/",
                        "cluster": {
                            "name": "backend",
                            "hosts": [{"address": "127.0.0.1", "port": 8080}],
                            "lb_policy": "ROUND_ROBIN",
                            "connect_timeout_seconds": 2,
                        },
                        "timeout_seconds": 10,
                        "retry_policy": {"retry_on": "5xx", "num_retries": 2},
                    }
                ],
            }
        ]
    }
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(data))
    return p


@pytest.fixture()
def bad_file(tmp_path: Path) -> Path:
    p = tmp_path / "bad.yaml"
    p.write_text(":::not valid yaml:::")
    return p


def test_build_parser_returns_parser():
    p = build_parser()
    assert p is not None


def test_main_returns_zero_for_valid_config(config_file):
    assert main([str(config_file)]) == 0


def test_main_returns_nonzero_for_missing_file():
    assert main(["nonexistent_file.yaml"]) == 1


def test_main_quiet_flag_produces_short_output(config_file, capsys):
    main([str(config_file), "--quiet"])
    out = capsys.readouterr().out.strip()
    # Should be a single line like "70/100 (70.0%)"
    assert "%" in out
    assert "\n" not in out


def test_main_full_output_contains_categories(config_file, capsys):
    main([str(config_file)])
    out = capsys.readouterr().out
    assert "Clusters" in out
    assert "Routes" in out
    assert "Listeners" in out


def test_main_min_score_pass(config_file):
    # A well-formed config should score above 0
    assert main([str(config_file), "--min-score", "1"]) == 0


def test_main_min_score_fail(config_file):
    # Require 100% — almost certainly fails
    assert main([str(config_file), "--min-score", "100"]) == 1
