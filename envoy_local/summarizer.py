"""Summarizer: produce a human-readable summary of a loaded EnvoyConfig."""

from dataclasses import dataclass
from typing import List

from envoy_local.config import EnvoyConfig


@dataclass
class ClusterSummary:
    name: str
    lb_policy: str
    host_count: int
    hosts: List[str]


@dataclass
class RouteSummary:
    name: str
    prefix: str
    cluster: str
    has_retry: bool
    timeout: float


@dataclass
class ListenerSummary:
    name: str
    address: str
    port: int
    route_count: int


@dataclass
class ConfigSummary:
    cluster_summaries: List[ClusterSummary]
    route_summaries: List[RouteSummary]
    listener_summaries: List[ListenerSummary]

    def as_text(self) -> str:
        lines: List[str] = []

        lines.append(f"Clusters ({len(self.cluster_summaries)}):")
        for c in self.cluster_summaries:
            lines.append(f"  [{c.name}] lb={c.lb_policy} hosts={c.host_count}")
            for h in c.hosts:
                lines.append(f"    - {h}")

        lines.append(f"Routes ({len(self.route_summaries)}):")
        for r in self.route_summaries:
            retry_flag = " retry=yes" if r.has_retry else ""
            lines.append(
                f"  [{r.name}] prefix={r.prefix} -> {r.cluster}"
                f" timeout={r.timeout}s{retry_flag}"
            )

        lines.append(f"Listeners ({len(self.listener_summaries)}):")
        for li in self.listener_summaries:
            lines.append(
                f"  [{li.name}] {li.address}:{li.port} routes={li.route_count}"
            )

        return "\n".join(lines)


def summarize_config(config: EnvoyConfig) -> ConfigSummary:
    """Build a ConfigSummary from an EnvoyConfig."""
    cluster_summaries = [
        ClusterSummary(
            name=c.name,
            lb_policy=c.lb_policy,
            host_count=len(c.hosts),
            hosts=[f"{h.address}:{h.port}" for h in c.hosts],
        )
        for c in config.clusters
    ]

    route_summaries = [
        RouteSummary(
            name=r.name,
            prefix=r.prefix,
            cluster=r.cluster,
            has_retry=r.retry_policy is not None,
            timeout=r.timeout,
        )
        for r in config.routes
    ]

    listener_summaries = [
        ListenerSummary(
            name=li.name,
            address=li.address,
            port=li.port,
            route_count=len(li.routes),
        )
        for li in config.listeners
    ]

    return ConfigSummary(
        cluster_summaries=cluster_summaries,
        route_summaries=route_summaries,
        listener_summaries=listener_summaries,
    )
