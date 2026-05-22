"""Core configuration models for Envoy proxy config generation."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class UpstreamHost:
    address: str
    port: int
    weight: int = 1


@dataclass
class ClusterConfig:
    name: str
    hosts: List[UpstreamHost]
    connect_timeout: str = "1s"
    lb_policy: str = "ROUND_ROBIN"

    def __post_init__(self):
        valid_policies = {"ROUND_ROBIN", "LEAST_REQUEST", "RANDOM", "RING_HASH"}
        if self.lb_policy not in valid_policies:
            raise ValueError(
                f"Invalid lb_policy '{self.lb_policy}'. Must be one of {valid_policies}"
            )
        if not self.hosts:
            raise ValueError("ClusterConfig must have at least one host.")


@dataclass
class RouteConfig:
    prefix: str
    cluster: str
    timeout: str = "15s"
    retry_on: Optional[str] = None
    num_retries: int = 0


@dataclass
class ListenerConfig:
    name: str
    address: str
    port: int
    routes: List[RouteConfig] = field(default_factory=list)
    stat_prefix: str = "ingress_http"


@dataclass
class EnvoyConfig:
    listeners: List[ListenerConfig] = field(default_factory=list)
    clusters: List[ClusterConfig] = field(default_factory=list)
    admin_port: int = 9901
    admin_address: str = "127.0.0.1"
