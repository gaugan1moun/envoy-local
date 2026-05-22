"""Validation utilities for Envoy local config objects."""

from dataclasses import dataclass
from typing import List

from envoy_local.config import ClusterConfig, ListenerConfig, RouteConfig


@dataclass
class ValidationError:
    field: str
    message: str

    def __str__(self) -> str:
        return f"[{self.field}] {self.message}"


def validate_cluster(cluster: ClusterConfig) -> List[ValidationError]:
    errors: List[ValidationError] = []

    if not cluster.name or not cluster.name.strip():
        errors.append(ValidationError("cluster.name", "Cluster name must not be empty."))

    if not cluster.hosts:
        errors.append(ValidationError("cluster.hosts", "Cluster must have at least one host."))

    for i, host in enumerate(cluster.hosts):
        if not host.address or not host.address.strip():
            errors.append(ValidationError(f"cluster.hosts[{i}].address", "Host address must not be empty."))
        if not (1 <= host.port <= 65535):
            errors.append(ValidationError(f"cluster.hosts[{i}].port", f"Port {host.port} is out of valid range (1-65535)."))

    valid_lb_policies = {"ROUND_ROBIN", "LEAST_REQUEST", "RANDOM", "RING_HASH"}
    if cluster.lb_policy not in valid_lb_policies:
        errors.append(ValidationError("cluster.lb_policy", f"lb_policy '{cluster.lb_policy}' is not valid. Choose from {valid_lb_policies}."))

    if cluster.connect_timeout_seconds <= 0:
        errors.append(ValidationError("cluster.connect_timeout_seconds", "connect_timeout_seconds must be positive."))

    return errors


def validate_route(route: RouteConfig) -> List[ValidationError]:
    errors: List[ValidationError] = []

    if not route.prefix or not route.prefix.startswith("/"):
        errors.append(ValidationError("route.prefix", "Route prefix must start with '/'"))

    if not route.cluster:
        errors.append(ValidationError("route.cluster", "Route must reference a cluster name."))

    if route.retry_on and route.num_retries is not None and route.num_retries < 0:
        errors.append(ValidationError("route.num_retries", "num_retries must be non-negative."))

    return errors


def validate_listener(listener: ListenerConfig) -> List[ValidationError]:
    errors: List[ValidationError] = []

    if not listener.name or not listener.name.strip():
        errors.append(ValidationError("listener.name", "Listener name must not be empty."))

    if not (1 <= listener.port <= 65535):
        errors.append(ValidationError("listener.port", f"Port {listener.port} is out of valid range (1-65535)."))

    if not listener.routes:
        errors.append(ValidationError("listener.routes", "Listener must have at least one route."))
    else:
        for i, route in enumerate(listener.routes):
            for err in validate_route(route):
                errors.append(ValidationError(f"listener.routes[{i}].{err.field}", err.message))

    return errors


def validate_all(listeners: List[ListenerConfig], clusters: List[ClusterConfig]) -> List[ValidationError]:
    errors: List[ValidationError] = []
    for cluster in clusters:
        errors.extend(validate_cluster(cluster))
    for listener in listeners:
        errors.extend(validate_listener(listener))
    return errors
