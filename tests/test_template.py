"""Tests for envoy_local.template."""

import pytest

from envoy_local.template import (
    apply_preset,
    list_presets,
    TemplateError,
    TemplateResult,
    PRESETS,
)


def test_list_presets_returns_all_names():
    names = list_presets()
    assert set(names) == set(PRESETS.keys())


def test_list_presets_is_sorted():
    names = list_presets()
    assert names == sorted(names)


def test_apply_unknown_preset_raises():
    with pytest.raises(TemplateError, match="Unknown preset"):
        apply_preset("nonexistent")


def test_apply_http_default_returns_result():
    result = apply_preset("http_default")
    assert isinstance(result, TemplateResult)
    assert result.preset_name == "http_default"


def test_http_default_cluster_overrides():
    result = apply_preset("http_default")
    assert result.cluster_overrides["lb_policy"] == "ROUND_ROBIN"
    assert "connect_timeout" in result.cluster_overrides


def test_http_default_has_retry_policy():
    result = apply_preset("http_default")
    assert "retry_policy" in result.route_overrides
    assert result.route_overrides["retry_policy"]["num_retries"] == 2


def test_grpc_default_lb_policy():
    result = apply_preset("grpc_default")
    assert result.cluster_overrides["lb_policy"] == "LEAST_REQUEST"


def test_static_strict_no_retry():
    result = apply_preset("static_strict")
    assert "retry_policy" not in result.route_overrides


def test_override_replaces_value():
    result = apply_preset("http_default", overrides={"max_retries": 5})
    assert result.route_overrides["retry_policy"]["num_retries"] == 5


def test_override_connect_timeout():
    result = apply_preset("http_default", overrides={"connect_timeout": "2s"})
    assert result.cluster_overrides["connect_timeout"] == "2s"


def test_as_dict_keys():
    result = apply_preset("http_default")
    d = result.as_dict()
    assert set(d.keys()) == {"preset", "cluster", "route"}


def test_as_dict_preset_name():
    result = apply_preset("grpc_default")
    assert result.as_dict()["preset"] == "grpc_default"


def test_none_overrides_uses_preset_defaults():
    r1 = apply_preset("http_default", overrides=None)
    r2 = apply_preset("http_default")
    assert r1.cluster_overrides == r2.cluster_overrides
