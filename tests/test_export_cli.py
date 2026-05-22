"""Tests for envoy_local.export_cli."""

from __future__ import annotations

import os
import yaml
import pytest

from envoy_local.export_cli import build_parser, main


MINIMAL_CONFIG = """
clusters:
  - name: web
    connect_timeout: 0.25s
    lb_policy: round_robin
    hosts:
      - address: 127.0.0.1
        port: 8080
listeners:
  - name: ingress
    address: 0.0.0.0
    port: 10000
    routes:
      - prefix: /
        cluster: web
"""


@pytest.fixture()
def config_file(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(MINIMAL_CONFIG, encoding="utf-8")
    return str(p)


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None
    assert parser.prog == "envoy-export"


def test_main_creates_output_file(config_file, tmp_path):
    out = str(tmp_path / "out" / "bootstrap.yaml")
    rc = main([config_file, "--output", out, "--quiet"])
    assert rc == 0
    assert os.path.isfile(out)


def test_main_output_is_valid_yaml(config_file, tmp_path):
    out = str(tmp_path / "bootstrap.yaml")
    main([config_file, "--output", out, "--quiet"])
    with open(out, encoding="utf-8") as fh:
        parsed = yaml.safe_load(fh)
    assert isinstance(parsed, dict)


def test_main_missing_input_returns_nonzero(tmp_path):
    out = str(tmp_path / "bootstrap.yaml")
    rc = main([str(tmp_path / "ghost.yaml"), "--output", out])
    assert rc != 0


def test_main_no_overwrite_flag_fails_on_existing(config_file, tmp_path):
    out = str(tmp_path / "bootstrap.yaml")
    main([config_file, "--output", out, "--quiet"])
    rc = main([config_file, "--output", out, "--no-overwrite"])
    assert rc != 0


def test_main_skip_validation_still_exports(config_file, tmp_path):
    out = str(tmp_path / "bootstrap.yaml")
    rc = main([config_file, "--output", out, "--skip-validation", "--quiet"])
    assert rc == 0
    assert os.path.isfile(out)


def test_main_prints_summary_without_quiet(config_file, tmp_path, capsys):
    out = str(tmp_path / "bootstrap.yaml")
    main([config_file, "--output", out])
    captured = capsys.readouterr()
    assert "Exported" in captured.out
