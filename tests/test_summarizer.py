"""Tests for envoy_local.summarizer."""

import pytest

from envoy_local.config import (
    ClusterConfig,
    EnvoyConfig,
    ListenerConfig,
    RouteConfig,
    UpstreamHost,
)
from envoy_local.summarizer import summarize_config


@pytest.fixture()
def full_config() -> EnvoyConfig:
    return EnvoyConfig(
        clusters=[
            ClusterConfig(
                name="svc-a",
                lb_policy="round_robin",
                hosts=[
                    UpstreamHost(address="10.0.0.1", port=8080),
                    UpstreamHost(address="10.0.0.2", port=8080),
                ],
            ),
            ClusterConfig(
                name="svc-b",
                lb_policy="least_request",
                hosts=[UpstreamHost(address="10.0.1.1", port=9090)],
            ),
        ],
        routes=[
            RouteConfig(
                name="route-a",
                prefix="/api",
                cluster="svc-a",
                timeout=5.0,
                retry_policy={"num_retries": 3},
            ),
            RouteConfig(
                name="route-b",
                prefix="/health",
                cluster="svc-b",
                timeout=1.0,
                retry_policy=None,
            ),
        ],
        listeners=[
            ListenerConfig(
                name="main",
                address="0.0.0.0",
                port=10000,
                routes=["route-a", "route-b"],
            )
        ],
    )


def test_cluster_summary_count(full_config):
    summary = summarize_config(full_config)
    assert len(summary.cluster_summaries) == 2


def test_cluster_summary_names(full_config):
    summary = summarize_config(full_config)
    names = [c.name for c in summary.cluster_summaries]
    assert "svc-a" in names
    assert "svc-b" in names


def test_cluster_host_count(full_config):
    summary = summarize_config(full_config)
    svc_a = next(c for c in summary.cluster_summaries if c.name == "svc-a")
    assert svc_a.host_count == 2


def test_cluster_host_strings(full_config):
    summary = summarize_config(full_config)
    svc_a = next(c for c in summary.cluster_summaries if c.name == "svc-a")
    assert "10.0.0.1:8080" in svc_a.hosts
    assert "10.0.0.2:8080" in svc_a.hosts


def test_route_summary_count(full_config):
    summary = summarize_config(full_config)
    assert len(summary.route_summaries) == 2


def test_route_retry_flag(full_config):
    summary = summarize_config(full_config)
    route_a = next(r for r in summary.route_summaries if r.name == "route-a")
    route_b = next(r for r in summary.route_summaries if r.name == "route-b")
    assert route_a.has_retry is True
    assert route_b.has_retry is False


def test_route_timeout(full_config):
    summary = summarize_config(full_config)
    route_a = next(r for r in summary.route_summaries if r.name == "route-a")
    assert route_a.timeout == 5.0


def test_listener_summary_count(full_config):
    summary = summarize_config(full_config)
    assert len(summary.listener_summaries) == 1


def test_listener_port(full_config):
    summary = summarize_config(full_config)
    assert summary.listener_summaries[0].port == 10000


def test_listener_route_count(full_config):
    summary = summarize_config(full_config)
    assert summary.listener_summaries[0].route_count == 2


def test_as_text_contains_cluster_names(full_config):
    text = summarize_config(full_config).as_text()
    assert "svc-a" in text
    assert "svc-b" in text


def test_as_text_contains_route_prefix(full_config):
    text = summarize_config(full_config).as_text()
    assert "/api" in text
    assert "/health" in text


def test_as_text_contains_listener_address(full_config):
    text = summarize_config(full_config).as_text()
    assert "0.0.0.0:10000" in text


def test_as_text_retry_flag_shown(full_config):
    text = summarize_config(full_config).as_text()
    assert "retry=yes" in text
