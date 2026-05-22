"""Tests for envoy_local.validator module."""

import pytest

from envoy_local.config import ClusterConfig, ListenerConfig, RouteConfig, UpstreamHost
from envoy_local.validator import (
    ValidationError,
    validate_all,
    validate_cluster,
    validate_listener,
    validate_route,
)


@pytest.fixture
def valid_cluster():
    return ClusterConfig(
        name="backend",
        hosts=[UpstreamHost(address="127.0.0.1", port=8080)],
        lb_policy="ROUND_ROBIN",
        connect_timeout_seconds=5,
    )


@pytest.fixture
def valid_route():
    return RouteConfig(prefix="/api", cluster="backend")


@pytest.fixture
def valid_listener(valid_route):
    return ListenerConfig(name="ingress", port=10000, routes=[valid_route])


def test_valid_cluster_no_errors(valid_cluster):
    assert validate_cluster(valid_cluster) == []


def test_cluster_empty_name():
    cluster = ClusterConfig(name="  ", hosts=[UpstreamHost(address="localhost", port=8080)])
    errors = validate_cluster(cluster)
    assert any("name" in e.field for e in errors)


def test_cluster_no_hosts():
    cluster = ClusterConfig(name="empty", hosts=[])
    errors = validate_cluster(cluster)
    assert any("hosts" in e.field for e in errors)


def test_cluster_invalid_port():
    cluster = ClusterConfig(name="bad_port", hosts=[UpstreamHost(address="localhost", port=99999)])
    errors = validate_cluster(cluster)
    assert any("port" in e.field for e in errors)


def test_cluster_invalid_lb_policy():
    cluster = ClusterConfig(
        name="bad_lb",
        hosts=[UpstreamHost(address="localhost", port=8080)],
        lb_policy="INVALID_POLICY",
    )
    errors = validate_cluster(cluster)
    assert any("lb_policy" in e.field for e in errors)


def test_cluster_zero_timeout():
    cluster = ClusterConfig(
        name="zero_timeout",
        hosts=[UpstreamHost(address="localhost", port=8080)],
        connect_timeout_seconds=0,
    )
    errors = validate_cluster(cluster)
    assert any("connect_timeout" in e.field for e in errors)


def test_valid_route_no_errors(valid_route):
    assert validate_route(valid_route) == []


def test_route_prefix_no_slash():
    route = RouteConfig(prefix="api", cluster="backend")
    errors = validate_route(route)
    assert any("prefix" in e.field for e in errors)


def test_route_missing_cluster():
    route = RouteConfig(prefix="/", cluster="")
    errors = validate_route(route)
    assert any("cluster" in e.field for e in errors)


def test_valid_listener_no_errors(valid_listener):
    assert validate_listener(valid_listener) == []


def test_listener_invalid_port(valid_route):
    listener = ListenerConfig(name="bad", port=0, routes=[valid_route])
    errors = validate_listener(listener)
    assert any("port" in e.field for e in errors)


def test_listener_no_routes():
    listener = ListenerConfig(name="empty", port=10000, routes=[])
    errors = validate_listener(listener)
    assert any("routes" in e.field for e in errors)


def test_validate_all_aggregates(valid_listener, valid_cluster):
    errors = validate_all([valid_listener], [valid_cluster])
    assert errors == []


def test_validation_error_str():
    err = ValidationError(field="cluster.name", message="must not be empty")
    assert "cluster.name" in str(err)
    assert "must not be empty" in str(err)
