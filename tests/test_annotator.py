"""Tests for envoy_local.annotator."""

import pytest

from envoy_local.config import UpstreamHost, ClusterConfig, RouteConfig, ListenerConfig
from envoy_local.annotator import (
    Annotation,
    AnnotationReport,
    annotate_cluster,
    annotate_route,
    annotate_listener,
    annotate_config,
)


@pytest.fixture()
def single_host_cluster() -> ClusterConfig:
    return ClusterConfig(
        name="backend",
        hosts=[UpstreamHost(address="127.0.0.1", port=9000)],
        lb_policy="ROUND_ROBIN",
    )


@pytest.fixture()
def multi_host_cluster() -> ClusterConfig:
    return ClusterConfig(
        name="api",
        hosts=[
            UpstreamHost(address="10.0.0.1", port=8080),
            UpstreamHost(address="10.0.0.2", port=8080),
        ],
        lb_policy="LEAST_REQUEST",
    )


@pytest.fixture()
def simple_route() -> RouteConfig:
    return RouteConfig(
        name="default-route",
        cluster="backend",
        prefix="/",
        timeout_seconds=30,
        retry_on="5xx",
        num_retries=3,
    )


@pytest.fixture()
def simple_listener(simple_route) -> ListenerConfig:
    return ListenerConfig(address="0.0.0.0", port=8080, routes=[simple_route])


# --- AnnotationReport ---

def test_report_add_and_retrieve():
    report = AnnotationReport()
    report.add("cluster:x", "host-count", "2 hosts")
    assert len(report.annotations) == 1
    assert report.annotations[0].tag == "host-count"


def test_report_by_tag_filters_correctly():
    report = AnnotationReport()
    report.add("cluster:x", "lb-policy", "round-robin")
    report.add("cluster:x", "host-count", "1 host")
    report.add("cluster:y", "lb-policy", "least-request")
    lb_annotations = report.by_tag("lb-policy")
    assert len(lb_annotations) == 2


def test_report_as_text_empty():
    report = AnnotationReport()
    assert report.as_text() == "No annotations."


def test_report_as_text_contains_tag():
    report = AnnotationReport()
    report.add("cluster:svc", "single-host", "Only one upstream")
    text = report.as_text()
    assert "single-host" in text
    assert "cluster:svc" in text


# --- annotate_cluster ---

def test_single_host_cluster_gets_single_host_tag(single_host_cluster):
    report = AnnotationReport()
    annotate_cluster(single_host_cluster, report)
    tags = [a.tag for a in report.annotations]
    assert "single-host" in tags


def test_multi_host_cluster_no_single_host_tag(multi_host_cluster):
    report = AnnotationReport()
    annotate_cluster(multi_host_cluster, report)
    tags = [a.tag for a in report.annotations]
    assert "single-host" not in tags


def test_cluster_lb_policy_annotation(multi_host_cluster):
    report = AnnotationReport()
    annotate_cluster(multi_host_cluster, report)
    lb = report.by_tag("lb-policy")
    assert len(lb) == 1
    assert "Least-request" in lb[0].detail


# --- annotate_route ---

def test_route_cluster_ref_annotation(simple_route):
    report = AnnotationReport()
    annotate_route(simple_route, report)
    refs = report.by_tag("cluster-ref")
    assert len(refs) == 1
    assert "backend" in refs[0].detail


def test_route_retry_annotation(simple_route):
    report = AnnotationReport()
    annotate_route(simple_route, report)
    retries = report.by_tag("retry")
    assert len(retries) == 1
    assert "5xx" in retries[0].detail


def test_route_timeout_annotation(simple_route):
    report = AnnotationReport()
    annotate_route(simple_route, report)
    timeouts = report.by_tag("timeout")
    assert len(timeouts) == 1
    assert "30" in timeouts[0].detail


# --- annotate_listener ---

def test_listener_bind_annotation(simple_listener):
    report = AnnotationReport()
    annotate_listener(simple_listener, report)
    binds = report.by_tag("bind")
    assert len(binds) == 1
    assert "8080" in binds[0].detail


def test_listener_routes_annotation(simple_listener):
    report = AnnotationReport()
    annotate_listener(simple_listener, report)
    routes = report.by_tag("routes")
    assert len(routes) == 1
    assert "default-route" in routes[0].detail


# --- annotate_config (integration) ---

def test_annotate_config_returns_report(single_host_cluster, simple_listener):
    report = annotate_config([single_host_cluster], [simple_listener])
    assert len(report.annotations) > 0


def test_annotate_config_covers_cluster_and_listener(single_host_cluster, simple_listener):
    report = annotate_config([single_host_cluster], [simple_listener])
    targets = {a.target for a in report.annotations}
    assert any("cluster:" in t for t in targets)
    assert any("listener:" in t for t in targets)
