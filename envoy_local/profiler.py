"""Profile Envoy bootstrap configs: report cluster/route/listener counts and complexity metrics."""

from dataclasses import dataclass, field
from typing import Dict, List

from envoy_local.config import EnvoyConfig


@dataclass
class ProfileResult:
    cluster_count: int = 0
    route_count: int = 0
    listener_count: int = 0
    total_upstream_hosts: int = 0
    retry_enabled_routes: int = 0
    tls_clusters: int = 0
    lb_policy_distribution: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Clusters      : {self.cluster_count}",
            f"Routes        : {self.route_count}",
            f"Listeners     : {self.listener_count}",
            f"Upstream hosts: {self.total_upstream_hosts}",
            f"Retry routes  : {self.retry_enabled_routes}",
            f"TLS clusters  : {self.tls_clusters}",
        ]
        if self.lb_policy_distribution:
            lb_str = ", ".join(
                f"{k}={v}" for k, v in sorted(self.lb_policy_distribution.items())
            )
            lines.append(f"LB policies   : {lb_str}")
        if self.warnings:
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        return "\n".join(lines)


def profile_config(config: "EnvoyConfig") -> ProfileResult:  # noqa: F821
    result = ProfileResult()

    result.cluster_count = len(config.clusters)
    result.route_count = len(config.routes)
    result.listener_count = len(config.listeners)

    for cluster in config.clusters:
        result.total_upstream_hosts += len(cluster.hosts)
        lb = getattr(cluster, "lb_policy", "round_robin") or "round_robin"
        result.lb_policy_distribution[lb] = result.lb_policy_distribution.get(lb, 0) + 1
        if getattr(cluster, "tls", False):
            result.tls_clusters += 1
        if not cluster.hosts:
            result.warnings.append(f"Cluster '{cluster.name}' has no upstream hosts.")

    for route in config.routes:
        if getattr(route, "retry_policy", None):
            result.retry_enabled_routes += 1

    if result.listener_count == 0:
        result.warnings.append("No listeners defined — proxy will not accept traffic.")

    return result
