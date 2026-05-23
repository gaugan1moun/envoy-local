"""Build a dependency graph of clusters, routes, and listeners."""
from dataclasses import dataclass, field
from typing import Dict, List, Set

from envoy_local.config import EnvoyConfig


@dataclass
class GraphNode:
    name: str
    kind: str  # 'listener' | 'route' | 'cluster'
    depends_on: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"GraphNode({self.kind}:{self.name})"


@dataclass
class ConfigGraph:
    nodes: Dict[str, GraphNode] = field(default_factory=dict)

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.name] = node

    def edges(self) -> List[tuple]:
        """Return (from, to) pairs representing dependencies."""
        result = []
        for node in self.nodes.values():
            for dep in node.depends_on:
                result.append((node.name, dep))
        return result

    def orphaned_clusters(self) -> List[str]:
        """Clusters not referenced by any route."""
        referenced: Set[str] = set()
        for node in self.nodes.values():
            if node.kind in ("route", "listener"):
                referenced.update(node.depends_on)
        return [
            n.name
            for n in self.nodes.values()
            if n.kind == "cluster" and n.name not in referenced
        ]

    def as_text(self) -> str:
        lines = ["Config Dependency Graph", "=" * 30]
        for node in self.nodes.values():
            dep_str = ", ".join(node.depends_on) if node.depends_on else "(none)"
            lines.append(f"  [{node.kind}] {node.name} -> {dep_str}")
        orphans = self.orphaned_clusters()
        if orphans:
            lines.append("")
            lines.append("Orphaned clusters (unreferenced):")
            for o in orphans:
                lines.append(f"  - {o}")
        return "\n".join(lines)


def build_graph(config: "EnvoyConfig") -> ConfigGraph:
    """Construct a ConfigGraph from an EnvoyConfig."""
    graph = ConfigGraph()

    for cluster in config.clusters:
        graph.add_node(GraphNode(name=cluster.name, kind="cluster"))

    for route in config.routes:
        graph.add_node(
            GraphNode(
                name=route.prefix,
                kind="route",
                depends_on=[route.cluster],
            )
        )

    for listener in config.listeners:
        route_deps = [r.prefix for r in config.routes if r.cluster]
        graph.add_node(
            GraphNode(
                name=f"{listener.address}:{listener.port}",
                kind="listener",
                depends_on=route_deps,
            )
        )

    return graph
