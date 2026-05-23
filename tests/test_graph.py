"""Tests for envoy_local.graph and envoy_local.graph_cli."""
import pytest

from envoy_local.config import (
    EnvoyConfig,
    ClusterConfig,
    RouteConfig,
    ListenerConfig,
    UpstreamHost,
)
from envoy_local.graph import build_graph, ConfigGraph, GraphNode


@pytest.fixture()
def full_config():
    return EnvoyConfig(
        clusters=[
            ClusterConfig(
                name="svc-a",
                hosts=[UpstreamHost(address="127.0.0.1", port=8080)],
            ),
            ClusterConfig(
                name="svc-b",
                hosts=[UpstreamHost(address="127.0.0.1", port=9090)],
            ),
        ],
        routes=[
            RouteConfig(prefix="/api", cluster="svc-a"),
        ],
        listeners=[
            ListenerConfig(address="0.0.0.0", port=10000),
        ],
    )


@pytest.fixture()
def graph(full_config):
    return build_graph(full_config)


def test_graph_has_cluster_nodes(graph):
    assert "svc-a" in graph.nodes
    assert graph.nodes["svc-a"].kind == "cluster"


def test_graph_has_route_node(graph):
    assert "/api" in graph.nodes
    assert graph.nodes["/api"].kind == "route"


def test_route_depends_on_cluster(graph):
    assert "svc-a" in graph.nodes["/api"].depends_on


def test_graph_has_listener_node(graph):
    assert "0.0.0.0:10000" in graph.nodes
    assert graph.nodes["0.0.0.0:10000"].kind == "listener"


def test_orphaned_cluster_detected(graph):
    orphans = graph.orphaned_clusters()
    assert "svc-b" in orphans


def test_no_orphan_when_all_referenced(full_config):
    full_config.routes.append(RouteConfig(prefix="/b", cluster="svc-b"))
    g = build_graph(full_config)
    assert g.orphaned_clusters() == []


def test_edges_returns_pairs(graph):
    edges = graph.edges()
    assert isinstance(edges, list)
    assert all(isinstance(e, tuple) and len(e) == 2 for e in edges)


def test_as_text_contains_cluster(graph):
    text = graph.as_text()
    assert "svc-a" in text


def test_as_text_contains_orphan_section(graph):
    text = graph.as_text()
    assert "Orphaned" in text
    assert "svc-b" in text


def test_as_text_no_orphan_section_when_none(full_config):
    full_config.routes.append(RouteConfig(prefix="/b", cluster="svc-b"))
    g = build_graph(full_config)
    text = g.as_text()
    assert "Orphaned" not in text


# --- CLI tests ---

def test_graph_cli_main_returns_zero(tmp_path, full_config):
    import yaml
    from envoy_local.graph_cli import main

    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text(
        yaml.dump({
            "clusters": [{"name": "svc-a", "hosts": [{"address": "127.0.0.1", "port": 8080}]}],
            "routes": [{"prefix": "/api", "cluster": "svc-a"}],
            "listeners": [{"address": "0.0.0.0", "port": 10000}],
        })
    )
    result = main([str(cfg_file)])
    assert result == 0


def test_graph_cli_orphans_only_nonzero_when_orphan(tmp_path):
    import yaml
    from envoy_local.graph_cli import main

    cfg_file = tmp_path / "cfg.yaml"
    cfg_file.write_text(
        yaml.dump({
            "clusters": [
                {"name": "svc-a", "hosts": [{"address": "127.0.0.1", "port": 8080}]},
                {"name": "svc-b", "hosts": [{"address": "127.0.0.1", "port": 9090}]},
            ],
            "routes": [{"prefix": "/api", "cluster": "svc-a"}],
            "listeners": [{"address": "0.0.0.0", "port": 10000}],
        })
    )
    result = main([str(cfg_file), "--orphans-only"])
    assert result == 1


def test_graph_cli_missing_file_returns_two():
    from envoy_local.graph_cli import main
    result = main(["nonexistent_file.yaml"])
    assert result == 2
