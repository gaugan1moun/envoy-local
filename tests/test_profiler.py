"""Tests for envoy_local.profiler and profile_cli."""

import pytest

from envoy_local.config import (
    ClusterConfig,
    EnvoyConfig,
    ListenerConfig,
    RouteConfig,
    UpstreamHost,
)
from envoy_local.profiler import profile_config


@pytest.fixture()
def full_config():
    return EnvoyConfig(
        clusters=[
            ClusterConfig(
                name="svc-a",
                hosts=[UpstreamHost(address="127.0.0.1", port=8080)],
                lb_policy="round_robin",
            ),
            ClusterConfig(
                name="svc-b",
                hosts=[
                    UpstreamHost(address="10.0.0.1", port=9090),
                    UpstreamHost(address="10.0.0.2", port=9090),
                ],
                lb_policy="least_request",
                tls=True,
            ),
        ],
        routes=[
            RouteConfig(name="route-a", prefix="/a", cluster="svc-a"),
            RouteConfig(
                name="route-b",
                prefix="/b",
                cluster="svc-b",
                retry_policy={"retry_on": "5xx", "num_retries": 3},
            ),
        ],
        listeners=[
            ListenerConfig(name="main", address="0.0.0.0", port=10000),
        ],
    )


def test_cluster_count(full_config):
    result = profile_config(full_config)
    assert result.cluster_count == 2


def test_route_count(full_config):
    result = profile_config(full_config)
    assert result.route_count == 2


def test_listener_count(full_config):
    result = profile_config(full_config)
    assert result.listener_count == 1


def test_total_upstream_hosts(full_config):
    result = profile_config(full_config)
    assert result.total_upstream_hosts == 3


def test_retry_enabled_routes(full_config):
    result = profile_config(full_config)
    assert result.retry_enabled_routes == 1


def test_tls_clusters(full_config):
    result = profile_config(full_config)
    assert result.tls_clusters == 1


def test_lb_policy_distribution(full_config):
    result = profile_config(full_config)
    assert result.lb_policy_distribution["round_robin"] == 1
    assert result.lb_policy_distribution["least_request"] == 1


def test_no_warnings_for_valid_config(full_config):
    result = profile_config(full_config)
    assert result.warnings == []


def test_warning_for_empty_hosts():
    config = EnvoyConfig(
        clusters=[ClusterConfig(name="empty", hosts=[])],
        routes=[],
        listeners=[ListenerConfig(name="l", address="0.0.0.0", port=10000)],
    )
    result = profile_config(config)
    assert any("empty" in w for w in result.warnings)


def test_warning_for_no_listeners():
    config = EnvoyConfig(
        clusters=[ClusterConfig(name="svc", hosts=[UpstreamHost("127.0.0.1", 8080)])],
        routes=[],
        listeners=[],
    )
    result = profile_config(config)
    assert any("listener" in w.lower() for w in result.warnings)


def test_summary_contains_counts(full_config):
    result = profile_config(full_config)
    summary = result.summary()
    assert "2" in summary  # clusters / routes
    assert "Clusters" in summary
    assert "Routes" in summary
