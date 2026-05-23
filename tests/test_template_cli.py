"""Tests for envoy_local.template_cli."""

import json
import pytest

from envoy_local.template_cli import build_parser, main


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None


def test_list_command_returns_zero():
    assert main(["list"]) == 0


def test_list_command_prints_presets(capsys):
    main(["list"])
    out = capsys.readouterr().out
    assert "http_default" in out
    assert "grpc_default" in out
    assert "static_strict" in out


def test_apply_known_preset_returns_zero():
    assert main(["apply", "http_default"]) == 0


def test_apply_unknown_preset_returns_nonzero():
    assert main(["apply", "no_such_preset"]) == 1


def test_apply_unknown_preset_prints_error(capsys):
    main(["apply", "bad_preset"])
    err = capsys.readouterr().err
    assert "error" in err.lower()


def test_apply_text_output_contains_preset_name(capsys):
    main(["apply", "grpc_default", "--format", "text"])
    out = capsys.readouterr().out
    assert "grpc_default" in out


def test_apply_json_output_is_valid_json(capsys):
    main(["apply", "http_default", "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["preset"] == "http_default"


def test_apply_json_output_has_cluster_key(capsys):
    main(["apply", "http_default", "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "cluster" in data


def test_apply_with_override_reflected_in_output(capsys):
    main(["apply", "http_default", "--override", "connect_timeout=9s", "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["cluster"]["connect_timeout"] == "9s"


def test_apply_bad_override_format_returns_nonzero():
    assert main(["apply", "http_default", "--override", "no_equals_sign"]) == 1


def test_no_command_returns_zero():
    # prints help, should not crash
    assert main([]) == 0
