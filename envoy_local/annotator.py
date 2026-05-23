"""Annotate a parsed Envoy config with human-readable metadata tags."""

from dataclasses import dataclass, field
from typing import List, Dict, Any

from envoy_local.config import ListenerConfig, ClusterConfig, RouteConfig


@dataclass
class Annotation:
    target: str  # e.g. "cluster:my-cluster", "listener:0.0.0.0:8080"
    tag: str
    detail: str = ""

    def __str__(self) -> str:
        parts = [f"[{self.tag}] {self.target}"]
        if self.detail:
            parts.append(f"  → {self.detail}")
        return "\n".join(parts)


@dataclass
class AnnotationReport:
    annotations: List[Annotation] = field(default_factory=list)

    def add(self, target: str, tag: str, detail: str = "") -> None:
        self.annotations.append(Annotation(target=target, tag=tag, detail=detail))

    def as_text(self) -> str:
        if not self.annotations:
            return "No annotations."
        return "\n".join(str(a) for a in self.annotations)

    def by_tag(self, tag: str) -> List[Annotation]:
        return [a for a in self.annotations if a.tag == tag]


def annotate_cluster(cluster: ClusterConfig, report: AnnotationReport) -> None:
    target = f"cluster:{cluster.name}"
    host_count = len(cluster.hosts)
    report.add(target, "host-count", f"{host_count} upstream host(s)")
    if host_count == 1:
        report.add(target, "single-host", "Only one upstream; no load balancing in effect")
    if cluster.lb_policy.upper() == "ROUND_ROBIN":
        report.add(target, "lb-policy", "Round-robin load balancing")
    elif cluster.lb_policy.upper() == "LEAST_REQUEST":
        report.add(target, "lb-policy", "Least-request load balancing")
    else:
        report.add(target, "lb-policy", f"Policy: {cluster.lb_policy}")


def annotate_route(route: RouteConfig, report: AnnotationReport) -> None:
    target = f"route:{route.name}"
    report.add(target, "cluster-ref", f"Routes to cluster '{route.cluster}'")
    if route.prefix:
        report.add(target, "match", f"Prefix match: {route.prefix}")
    if route.timeout_seconds is not None:
        report.add(target, "timeout", f"{route.timeout_seconds}s request timeout")
    if route.retry_on:
        report.add(target, "retry", f"Retries on: {route.retry_on} (max {route.num_retries})")


def annotate_listener(listener: ListenerConfig, report: AnnotationReport) -> None:
    target = f"listener:{listener.address}:{listener.port}"
    report.add(target, "bind", f"Listening on {listener.address}:{listener.port}")
    route_names = [r.name for r in listener.routes]
    report.add(target, "routes", f"{len(route_names)} route(s): {', '.join(route_names)}")


def annotate_config(
    clusters: List[ClusterConfig],
    listeners: List[ListenerConfig],
) -> AnnotationReport:
    report = AnnotationReport()
    for cluster in clusters:
        annotate_cluster(cluster, report)
    for listener in listeners:
        annotate_listener(listener, report)
        for route in listener.routes:
            annotate_route(route, report)
    return report
