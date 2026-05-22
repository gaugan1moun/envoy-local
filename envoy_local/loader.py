"""Load an envoy-local YAML/JSON config file into dataclass instances."""

import json
from pathlib import Path
from typing import Any, Dict

import yaml

from envoy_local.config import (
    ClusterConfig,
    ListenerConfig,
    RouteConfig,
    UpstreamHost,
)


def _parse_upstream(raw: Dict[str, Any]) -> UpstreamHost:
    return UpstreamHost(address=raw["address"], port=int(raw["port"]))


def _parse_cluster(raw: Dict[str, Any]) -> ClusterConfig:
    hosts = [_parse_upstream(h) for h in raw.get("hosts", [])]
    return ClusterConfig(
        name=raw["name"],
        hosts=hosts,
        lb_policy=raw.get("lb_policy", "ROUND_ROBIN"),
        connect_timeout=raw.get("connect_timeout", "5s"),
    )


def _parse_route(raw: Dict[str, Any]) -> RouteConfig:
    return RouteConfig(
        prefix=raw["prefix"],
        cluster=raw["cluster"],
        timeout=raw.get("timeout", "15s"),
        retry_on=raw.get("retry_on"),
        num_retries=raw.get("num_retries"),
    )


def _parse_listener(raw: Dict[str, Any]) -> ListenerConfig:
    routes = [_parse_route(r) for r in raw.get("routes", [])]
    return ListenerConfig(
        name=raw["name"],
        address=raw.get("address", "0.0.0.0"),
        port=int(raw["port"]),
        routes=routes,
    )


def load_config(path: Path) -> Dict[str, Any]:
    """Return a dict with 'clusters' and 'listeners' dataclass lists."""
    path = Path(path)
    text = path.read_text()
    if path.suffix in (".json",):
        raw = json.loads(text)
    else:
        raw = yaml.safe_load(text)

    return {
        "clusters": [_parse_cluster(c) for c in raw.get("clusters", [])],
        "listeners": [_parse_listener(l) for l in raw.get("listeners", [])],
    }
