"""Inspector: analyse a loaded EnvoyConfig and surface runtime insights."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envoy_local.config import ListenerConfig


@dataclass
class InspectorIssue:
    severity: str  # 'info' | 'warning' | 'error'
    component: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.component}: {self.message}"


@dataclass
class InspectionResult:
    issues: List[InspectorIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[InspectorIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[InspectorIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def infos(self) -> List[InspectorIssue]:
        return [i for i in self.issues if i.severity == "info"]

    def as_text(self) -> str:
        if not self.issues:
            return "No issues found."
        return "\n".join(str(i) for i in self.issues)

    def summary(self) -> str:
        return (
            f"{len(self.errors)} error(s), "
            f"{len(self.warnings)} warning(s), "
            f"{len(self.infos)} info(s)"
        )


def inspect_config(listeners: List[ListenerConfig]) -> InspectionResult:
    """Run all inspection checks and return an InspectionResult."""
    result = InspectionResult()

    if not listeners:
        result.issues.append(
            InspectorIssue("error", "config", "No listeners defined.")
        )
        return result

    seen_ports: dict[int, str] = {}

    for listener in listeners:
        name = listener.name

        # Duplicate port check
        if listener.port in seen_ports:
            result.issues.append(
                InspectorIssue(
                    "error",
                    f"listener:{name}",
                    f"Port {listener.port} already used by '{seen_ports[listener.port]}'.",
                )
            )
        else:
            seen_ports[listener.port] = name

        # No routes check
        if not listener.routes:
            result.issues.append(
                InspectorIssue(
                    "warning",
                    f"listener:{name}",
                    "Listener has no routes configured.",
                )
            )
            continue

        for route in listener.routes:
            # Cluster reference present
            if not route.cluster:
                result.issues.append(
                    InspectorIssue(
                        "error",
                        f"listener:{name}/route:{route.prefix}",
                        "Route has no cluster assigned.",
                    )
                )

            # Timeout sanity
            if route.timeout_seconds is not None and route.timeout_seconds <= 0:
                result.issues.append(
                    InspectorIssue(
                        "warning",
                        f"listener:{name}/route:{route.prefix}",
                        f"Timeout value {route.timeout_seconds}s is not positive.",
                    )
                )

            # Retry sanity
            if route.retry_attempts is not None and route.retry_attempts < 0:
                result.issues.append(
                    InspectorIssue(
                        "warning",
                        f"listener:{name}/route:{route.prefix}",
                        f"retry_attempts {route.retry_attempts} is negative.",
                    )
                )

    result.issues.append(
        InspectorIssue(
            "info",
            "config",
            f"Inspected {len(listeners)} listener(s) on port(s): "
            + ", ".join(str(p) for p in sorted(seen_ports)),
        )
    )

    return result
