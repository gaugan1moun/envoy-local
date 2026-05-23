"""Tests for envoy_local.scorer."""
import pytest

from envoy_local.config import (
    ClusterConfig,
    ListenerConfig,
    RouteConfig,
    UpstreamHost,
)
from envoy_local.scorer import ScoreResult, score_config


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def full_listeners():
    cluster = ClusterConfig(
        name="backend",
        hosts=[UpstreamHost(address="127.0.0.1", port=8080)],
        lb_policy="ROUND_ROBIN",
        connect_timeout_seconds=3,
    )
    route = RouteConfig(
        match_prefix="/",
        cluster=cluster,
        timeout_seconds=10,
        retry_policy={"retry_on": "5xx", "num_retries": 3},
    )
    listener = ListenerConfig(name="ingress", port=10000, routes=[route])
    return [listener]


@pytest.fixture()
def empty_listeners():
    return []


# ---------------------------------------------------------------------------
# ScoreResult helpers
# ---------------------------------------------------------------------------

def test_score_result_percentage_zero_when_no_categories():
    r = ScoreResult(categories=[])
    assert r.percentage == 0.0


def test_score_result_total_sums_categories(full_listeners):
    result = score_config(full_listeners)
    assert result.total == sum(c.score for c in result.categories)


def test_score_result_max_total(full_listeners):
    result = score_config(full_listeners)
    assert result.max_total == 100


def test_summary_contains_percentage(full_listeners):
    result = score_config(full_listeners)
    assert "%" in result.summary()


def test_summary_contains_category_names(full_listeners):
    result = score_config(full_listeners)
    text = result.summary()
    assert "Clusters" in text
    assert "Routes" in text
    assert "Listeners" in text


# ---------------------------------------------------------------------------
# Full config scoring
# ---------------------------------------------------------------------------

def test_full_config_scores_above_zero(full_listeners):
    result = score_config(full_listeners)
    assert result.total > 0


def test_full_config_percentage_positive(full_listeners):
    result = score_config(full_listeners)
    assert result.percentage > 0


# ---------------------------------------------------------------------------
# Empty / degenerate configs
# ---------------------------------------------------------------------------

def test_empty_listeners_score_zero(empty_listeners):
    result = score_config(empty_listeners)
    assert result.total == 0


def test_empty_listeners_notes_mention_no_listeners(empty_listeners):
    result = score_config(empty_listeners)
    listener_cat = next(c for c in result.categories if c.name == "Listeners")
    assert any("No listeners" in n for n in listener_cat.notes)


# ---------------------------------------------------------------------------
# Penalty cases
# ---------------------------------------------------------------------------

def test_high_timeout_cluster_penalised():
    cluster = ClusterConfig(
        name="slow",
        hosts=[UpstreamHost(address="10.0.0.1", port=9000)],
        lb_policy="ROUND_ROBIN",
        connect_timeout_seconds=30,
    )
    route = RouteConfig(
        match_prefix="/slow",
        cluster=cluster,
        timeout_seconds=5,
        retry_policy={"retry_on": "5xx"},
    )
    listener = ListenerConfig(name="l", port=8080, routes=[route])
    result = score_config([listener])
    cluster_cat = next(c for c in result.categories if c.name == "Clusters")
    assert any("connect_timeout" in n for n in cluster_cat.notes)


def test_missing_retry_policy_noted():
    cluster = ClusterConfig(
        name="c",
        hosts=[UpstreamHost(address="1.2.3.4", port=80)],
        lb_policy="ROUND_ROBIN",
        connect_timeout_seconds=1,
    )
    route = RouteConfig(
        match_prefix="/",
        cluster=cluster,
        timeout_seconds=5,
        retry_policy=None,
    )
    listener = ListenerConfig(name="l", port=10000, routes=[route])
    result = score_config([listener])
    route_cat = next(c for c in result.categories if c.name == "Routes")
    assert any("retry" in n.lower() for n in route_cat.notes)
