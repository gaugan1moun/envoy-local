"""Tests for envoy_local.inspector."""
import pytest

from envoy_local.config import ClusterConfig, ListenerConfig, RouteConfig, UpstreamHost
from envoy_local.inspector import InspectionResult, InspectorIssue, inspect_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _host(host="127.0.0.1", port=8080):
    return UpstreamHost(address=host, port=port)


def _route(prefix="/", cluster="svc", timeout=30, retries=2):
    return RouteConfig(
        prefix=prefix,
        cluster=cluster,
        timeout_seconds=timeout,
        retry_attempts=retries,
    )


def _listener(name="front", port=10000, routes=None):
    return ListenerConfig(
        name=name,
        port=port,
        routes=routes if routes is not None else [_route()],
    )


# ---------------------------------------------------------------------------
# InspectorIssue / InspectionResult unit tests
# ---------------------------------------------------------------------------

def test_issue_str():
    issue = InspectorIssue("error", "comp", "bad thing")
    assert "ERROR" in str(issue)
    assert "comp" in str(issue)
    assert "bad thing" in str(issue)


def test_result_filters():
    result = InspectionResult(
        issues=[
            InspectorIssue("error", "a", "e"),
            InspectorIssue("warning", "b", "w"),
            InspectorIssue("info", "c", "i"),
        ]
    )
    assert len(result.errors) == 1
    assert len(result.warnings) == 1
    assert len(result.infos) == 1


def test_result_as_text_no_issues():
    result = InspectionResult()
    assert "No issues" in result.as_text()


def test_result_summary_counts():
    result = InspectionResult(
        issues=[
            InspectorIssue("error", "a", "e"),
            InspectorIssue("warning", "b", "w"),
        ]
    )
    summary = result.summary()
    assert "1 error" in summary
    assert "1 warning" in summary


# ---------------------------------------------------------------------------
# inspect_config tests
# ---------------------------------------------------------------------------

def test_no_listeners_returns_error():
    result = inspect_config([])
    assert any(i.severity == "error" for i in result.issues)


def test_valid_single_listener_no_errors():
    result = inspect_config([_listener()])
    assert result.errors == []


def test_valid_single_listener_has_info():
    result = inspect_config([_listener()])
    assert result.infos  # should always emit an info summary


def test_duplicate_port_raises_error():
    l1 = _listener(name="a", port=9000)
    l2 = _listener(name="b", port=9000)
    result = inspect_config([l1, l2])
    errors = [i for i in result.errors if "Port 9000" in i.message]
    assert errors


def test_listener_no_routes_is_warning():
    listener = _listener(routes=[])
    result = inspect_config([listener])
    assert any(i.severity == "warning" and "no routes" in i.message.lower() for i in result.issues)


def test_route_no_cluster_is_error():
    bad_route = RouteConfig(prefix="/", cluster="", timeout_seconds=30, retry_attempts=2)
    listener = _listener(routes=[bad_route])
    result = inspect_config([listener])
    assert result.errors


def test_negative_timeout_is_warning():
    bad_route = _route(timeout=-1)
    listener = _listener(routes=[bad_route])
    result = inspect_config([listener])
    warnings = [i for i in result.warnings if "Timeout" in i.message]
    assert warnings


def test_negative_retries_is_warning():
    bad_route = _route(retries=-3)
    listener = _listener(routes=[bad_route])
    result = inspect_config([listener])
    warnings = [i for i in result.warnings if "retry_attempts" in i.message]
    assert warnings


def test_info_lists_all_ports():
    l1 = _listener(name="a", port=9000)
    l2 = _listener(name="b", port=9001)
    result = inspect_config([l1, l2])
    info_texts = " ".join(i.message for i in result.infos)
    assert "9000" in info_texts
    assert "9001" in info_texts
