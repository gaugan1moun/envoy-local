"""Tests for envoy_local.linter."""

import pytest

from envoy_local.config import ClusterConfig, ListenerConfig, RouteConfig, UpstreamHost
from envoy_local.linter import (
    LintResult,
    LintWarning,
    lint_cluster,
    lint_config,
    lint_listener,
    lint_route,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def good_cluster():
    return ClusterConfig(
        name="svc-a",
        hosts=[UpstreamHost(address="10.0.0.1", port=8080)],
        lb_policy="ROUND_ROBIN",
        connect_timeout_ms=250,
    )


@pytest.fixture
def good_route():
    return RouteConfig(prefix="/api", cluster="svc-a", timeout_ms=3000, retry_on=None, num_retries=None)


@pytest.fixture
def good_listener(good_route):
    return ListenerConfig(name="ingress", port=10000, routes=[good_route])


# ---------------------------------------------------------------------------
# lint_cluster
# ---------------------------------------------------------------------------

def test_lint_cluster_no_issues(good_cluster):
    assert lint_cluster(good_cluster) == []


def test_lint_cluster_no_hosts():
    cluster = ClusterConfig(name="empty", hosts=[], lb_policy="ROUND_ROBIN", connect_timeout_ms=250)
    issues = lint_cluster(cluster)
    assert any(w.level == "error" and "no upstream hosts" in w.message.lower() for w in issues)


def test_lint_cluster_invalid_port():
    cluster = ClusterConfig(
        name="bad-port",
        hosts=[UpstreamHost(address="10.0.0.1", port=99999)],
        lb_policy="ROUND_ROBIN",
        connect_timeout_ms=250,
    )
    issues = lint_cluster(cluster)
    assert any(w.level == "error" and "invalid port" in w.message.lower() for w in issues)


def test_lint_cluster_high_timeout_is_warning():
    cluster = ClusterConfig(
        name="slow",
        hosts=[UpstreamHost(address="10.0.0.1", port=8080)],
        lb_policy="ROUND_ROBIN",
        connect_timeout_ms=60_000,
    )
    issues = lint_cluster(cluster)
    assert any(w.level == "warning" and "unusually high" in w.message.lower() for w in issues)


# ---------------------------------------------------------------------------
# lint_route
# ---------------------------------------------------------------------------

def test_lint_route_no_issues(good_route):
    assert lint_route(good_route) == []


def test_lint_route_negative_timeout():
    route = RouteConfig(prefix="/bad", cluster="svc-a", timeout_ms=-1, retry_on=None, num_retries=None)
    issues = lint_route(route)
    assert any(w.level == "error" and "negative" in w.message.lower() for w in issues)


def test_lint_route_retry_without_num_retries():
    route = RouteConfig(prefix="/retry", cluster="svc-a", timeout_ms=1000, retry_on="5xx", num_retries=0)
    issues = lint_route(route)
    assert any(w.level == "warning" and "num_retries" in w.message.lower() for w in issues)


def test_lint_route_prefix_missing_slash():
    route = RouteConfig(prefix="api", cluster="svc-a", timeout_ms=500, retry_on=None, num_retries=None)
    issues = lint_route(route)
    assert any("prefix" in w.message.lower() or "'/'" in w.message for w in issues)


# ---------------------------------------------------------------------------
# lint_listener
# ---------------------------------------------------------------------------

def test_lint_listener_no_issues(good_listener):
    assert lint_listener(good_listener) == []


def test_lint_listener_no_routes():
    listener = ListenerConfig(name="empty", port=10000, routes=[])
    issues = lint_listener(listener)
    assert any(w.level == "warning" and "no routes" in w.message.lower() for w in issues)


# ---------------------------------------------------------------------------
# lint_config
# ---------------------------------------------------------------------------

def test_lint_config_unknown_cluster_is_error(good_listener, good_cluster):
    # route references 'svc-a' but we pass a cluster named 'other'
    other_cluster = ClusterConfig(
        name="other",
        hosts=[UpstreamHost(address="10.0.0.2", port=9090)],
        lb_policy="ROUND_ROBIN",
        connect_timeout_ms=250,
    )
    result = lint_config([good_listener], [other_cluster])
    assert result.has_errors
    assert any("unknown cluster" in w.message.lower() for w in result.warnings)


def test_lint_config_clean(good_listener, good_cluster):
    result = lint_config([good_listener], [good_cluster])
    assert not result.has_errors
    assert not result.has_warnings


def test_lint_result_summary_format():
    result = LintResult(warnings=[
        LintWarning("error", "x", "bad"),
        LintWarning("warning", "y", "meh"),
    ])
    assert "1 error" in result.summary()
    assert "1 warning" in result.summary()


def test_lint_warning_str():
    w = LintWarning("error", "cluster:foo", "Something wrong.")
    assert "[ERROR]" in str(w)
    assert "cluster:foo" in str(w)
