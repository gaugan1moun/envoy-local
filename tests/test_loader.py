"""Tests for envoy_local.loader."""

import json
import textwrap
from pathlib import Path

import pytest
import yaml

from envoy_local.loader import load_config
from envoy_local.config import ClusterConfig, ListenerConfig


SAMPLE = {
    "clusters": [
        {
            "name": "backend",
            "hosts": [{"address": "127.0.0.1", "port": 8080}],
            "lb_policy": "LEAST_REQUEST",
        }
    ],
    "listeners": [
        {
            "name": "ingress",
            "port": 10000,
            "routes": [
                {"prefix": "/api", "cluster": "backend", "timeout": "10s"}
            ],
        }
    ],
}


@pytest.fixture()
def yaml_file(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(SAMPLE))
    return p


@pytest.fixture()
def json_file(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps(SAMPLE))
    return p


def test_load_yaml_clusters(yaml_file):
    cfg = load_config(yaml_file)
    assert len(cfg["clusters"]) == 1
    cluster = cfg["clusters"][0]
    assert isinstance(cluster, ClusterConfig)
    assert cluster.name == "backend"
    assert cluster.lb_policy == "LEAST_REQUEST"


def test_load_yaml_hosts(yaml_file):
    cfg = load_config(yaml_file)
    host = cfg["clusters"][0].hosts[0]
    assert host.address == "127.0.0.1"
    assert host.port == 8080


def test_load_yaml_listeners(yaml_file):
    cfg = load_config(yaml_file)
    assert len(cfg["listeners"]) == 1
    listener = cfg["listeners"][0]
    assert isinstance(listener, ListenerConfig)
    assert listener.port == 10000


def test_load_yaml_routes(yaml_file):
    cfg = load_config(yaml_file)
    route = cfg["listeners"][0].routes[0]
    assert route.prefix == "/api"
    assert route.cluster == "backend"
    assert route.timeout == "10s"


def test_load_json_file(json_file):
    cfg = load_config(json_file)
    assert cfg["clusters"][0].name == "backend"
    assert cfg["listeners"][0].name == "ingress"


def test_missing_file_raises(tmp_path):
    with pytest.raises(OSError):
        load_config(tmp_path / "nonexistent.yaml")
