"""Tests for config builder and YAML renderer."""

import pytest
import yaml

from envoy_local.builder import build_bootstrap
from envoy_local.config import (
    ClusterConfig,
    EnvoyConfig,
    ListenerConfig,
    RouteConfig,
    UpstreamHost,
)
from envoy_local.renderer import render_yaml, write_yaml


@pytest.fixture()
def simple_config() -> EnvoyConfig:
    cluster = ClusterConfig(
        name="backend",
        hosts=[UpstreamHost(address="127.0.0.1", port=8080)],
    )
    listener = ListenerConfig(
        name="listener_0",
        address="0.0.0.0",
        port=10000,
        routes=[
            RouteConfig(prefix="/", cluster="backend"),
            RouteConfig(
                prefix="/retry",
                cluster="backend",
                retry_on="5xx",
                num_retries=3,
            ),
        ],
    )
    return EnvoyConfig(listeners=[listener], clusters=[cluster])


def test_build_bootstrap_structure(simple_config):
    bootstrap = build_bootstrap(simple_config)
    assert "admin" in bootstrap
    assert "static_resources" in bootstrap
    sr = bootstrap["static_resources"]
    assert len(sr["listeners"]) == 1
    assert len(sr["clusters"]) == 1


def test_cluster_name_and_lb(simple_config):
    bootstrap = build_bootstrap(simple_config)
    cluster = bootstrap["static_resources"]["clusters"][0]
    assert cluster["name"] == "backend"
    assert cluster["lb_policy"] == "ROUND_ROBIN"


def test_route_retry_policy(simple_config):
    bootstrap = build_bootstrap(simple_config)
    vhosts = (
        bootstrap["static_resources"]["listeners"][0]["filter_chains"][0]["filters"][0]
        ["typed_config"]["route_config"]["virtual_hosts"]
    )
    routes = vhosts[0]["routes"]
    retry_route = next(r for r in routes if r["match"]["prefix"] == "/retry")
    assert retry_route["route"]["retry_policy"]["num_retries"] == 3


def test_render_yaml_is_valid_yaml(simple_config):
    raw = render_yaml(simple_config)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    assert "static_resources" in parsed


def test_write_yaml_creates_file(simple_config, tmp_path):
    out = tmp_path / "out" / "bootstrap.yaml"
    result = write_yaml(simple_config, output=out)
    assert result == out
    assert out.exists()
    content = yaml.safe_load(out.read_text())
    assert content["admin"]["address"]["socket_address"]["port_value"] == 9901


def test_invalid_lb_policy():
    with pytest.raises(ValueError, match="Invalid lb_policy"):
        ClusterConfig(
            name="bad",
            hosts=[UpstreamHost("localhost", 8080)],
            lb_policy="INVALID",
        )


def test_empty_hosts_raises():
    with pytest.raises(ValueError, match="at least one host"):
        ClusterConfig(name="empty", hosts=[])
