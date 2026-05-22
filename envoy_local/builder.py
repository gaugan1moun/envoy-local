"""Builds Envoy bootstrap YAML config from EnvoyConfig dataclasses."""

from typing import Any, Dict

from envoy_local.config import ClusterConfig, EnvoyConfig, ListenerConfig, RouteConfig


def _build_route(route: RouteConfig) -> Dict[str, Any]:
    match = {"prefix": route.prefix}
    action: Dict[str, Any] = {
        "cluster": route.cluster,
        "timeout": route.timeout,
    }
    if route.retry_on and route.num_retries > 0:
        action["retry_policy"] = {
            "retry_on": route.retry_on,
            "num_retries": route.num_retries,
        }
    return {"match": match, "route": action}


def _build_listener(listener: ListenerConfig) -> Dict[str, Any]:
    routes = [_build_route(r) for r in listener.routes]
    return {
        "name": listener.name,
        "address": {
            "socket_address": {"address": listener.address, "port_value": listener.port}
        },
        "filter_chains": [
            {
                "filters": [
                    {
                        "name": "envoy.filters.network.http_connection_manager",
                        "typed_config": {
                            "@type": "type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager",
                            "stat_prefix": listener.stat_prefix,
                            "route_config": {
                                "name": "local_route",
                                "virtual_hosts": [
                                    {
                                        "name": "local_service",
                                        "domains": ["*"],
                                        "routes": routes,
                                    }
                                ],
                            },
                            "http_filters": [{"name": "envoy.filters.http.router"}],
                        },
                    }
                ]
            }
        ],
    }


def _build_cluster(cluster: ClusterConfig) -> Dict[str, Any]:
    endpoints = [
        {
            "lb_endpoints": [
                {
                    "endpoint": {
                        "address": {
                            "socket_address": {
                                "address": h.address,
                                "port_value": h.port,
                            }
                        }
                    },
                    "load_balancing_weight": h.weight,
                }
                for h in cluster.hosts
            ]
        }
    ]
    return {
        "name": cluster.name,
        "connect_timeout": cluster.connect_timeout,
        "type": "STRICT_DNS",
        "lb_policy": cluster.lb_policy,
        "load_assignment": {
            "cluster_name": cluster.name,
            "endpoints": endpoints,
        },
    }


def build_bootstrap(cfg: EnvoyConfig) -> Dict[str, Any]:
    """Return a dict representing the Envoy bootstrap config."""
    return {
        "admin": {
            "address": {
                "socket_address": {
                    "address": cfg.admin_address,
                    "port_value": cfg.admin_port,
                }
            }
        },
        "static_resources": {
            "listeners": [_build_listener(l) for l in cfg.listeners],
            "clusters": [_build_cluster(c) for c in cfg.clusters],
        },
    }
