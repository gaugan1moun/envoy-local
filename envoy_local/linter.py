"""Linter for envoy-local configs — checks for common misconfigurations."""

from dataclasses import dataclass, field
from typing import List

from envoy_local.config import ListenerConfig, ClusterConfig, RouteConfig


@dataclass
class LintWarning:
    level: str  # 'error' | 'warning' | 'info'
    location: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level.upper()}] {self.location}: {self.message}"


@dataclass
class LintResult:
    warnings: List[LintWarning] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(w.level == "error" for w in self.warnings)

    @property
    def has_warnings(self) -> bool:
        return any(w.level == "warning" for w in self.warnings)

    def summary(self) -> str:
        errors = sum(1 for w in self.warnings if w.level == "error")
        warnings = sum(1 for w in self.warnings if w.level == "warning")
        return f"{errors} error(s), {warnings} warning(s)"


def lint_cluster(cluster: ClusterConfig) -> List[LintWarning]:
    issues: List[LintWarning] = []
    loc = f"cluster:{cluster.name}"

    if not cluster.hosts:
        issues.append(LintWarning("error", loc, "Cluster has no upstream hosts."))

    for host in cluster.hosts:
        if host.port < 1 or host.port > 65535:
            issues.append(LintWarning("error", loc, f"Host '{host.address}' has invalid port {host.port}."))
        if host.address in ("localhost", "127.0.0.1") and len(cluster.hosts) > 1:
            issues.append(LintWarning("warning", loc, f"Loopback address '{host.address}' mixed with other hosts."))

    if cluster.connect_timeout_ms < 1:
        issues.append(LintWarning("error", loc, "connect_timeout_ms must be >= 1."))
    elif cluster.connect_timeout_ms > 30_000:
        issues.append(LintWarning("warning", loc, "connect_timeout_ms > 30s is unusually high."))

    return issues


def lint_route(route: RouteConfig) -> List[LintWarning]:
    issues: List[LintWarning] = []
    loc = f"route:{route.prefix}"

    if route.timeout_ms is not None and route.timeout_ms < 0:
        issues.append(LintWarning("error", loc, "timeout_ms must not be negative."))

    if route.retry_on and (route.num_retries is None or route.num_retries < 1):
        issues.append(LintWarning("warning", loc, "retry_on is set but num_retries is missing or < 1."))

    if not route.prefix.startswith("/"):
        issues.append(LintWarning("warning", loc, "Route prefix should start with '/'." ))

    return issues


def lint_listener(listener: ListenerConfig) -> List[LintWarning]:
    issues: List[LintWarning] = []
    loc = f"listener:{listener.name}"

    if listener.port < 1 or listener.port > 65535:
        issues.append(LintWarning("error", loc, f"Invalid port {listener.port}."))

    if not listener.routes:
        issues.append(LintWarning("warning", loc, "Listener has no routes defined."))

    for route in listener.routes:
        issues.extend(lint_route(route))

    return issues


def lint_config(listeners: List[ListenerConfig], clusters: List[ClusterConfig]) -> LintResult:
    result = LintResult()

    cluster_names = {c.name for c in clusters}
    for listener in listeners:
        result.warnings.extend(lint_listener(listener))
        for route in listener.routes:
            if route.cluster not in cluster_names:
                result.warnings.append(
                    LintWarning("error", f"route:{route.prefix}",
                                f"References unknown cluster '{route.cluster}'.")
                )

    for cluster in clusters:
        result.warnings.extend(lint_cluster(cluster))

    return result
