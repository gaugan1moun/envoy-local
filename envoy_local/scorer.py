"""Score an Envoy config on readiness/best-practice dimensions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envoy_local.config import ListenerConfig


@dataclass
class ScoreCategory:
    name: str
    score: int          # 0-100
    max_score: int
    notes: List[str] = field(default_factory=list)


@dataclass
class ScoreResult:
    categories: List[ScoreCategory] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(c.score for c in self.categories)

    @property
    def max_total(self) -> int:
        return sum(c.max_score for c in self.categories)

    @property
    def percentage(self) -> float:
        if self.max_total == 0:
            return 0.0
        return round(self.total / self.max_total * 100, 1)

    def summary(self) -> str:
        lines = [f"Config score: {self.total}/{self.max_total} ({self.percentage}%)", ""]
        for cat in self.categories:
            lines.append(f"  [{cat.score}/{cat.max_score}] {cat.name}")
            for note in cat.notes:
                lines.append(f"      - {note}")
        return "\n".join(lines)


def _score_clusters(listeners: List[ListenerConfig]) -> ScoreCategory:
    cat = ScoreCategory(name="Clusters", score=0, max_score=40)
    clusters = [r.cluster for ln in listeners for r in ln.routes]
    if not clusters:
        cat.notes.append("No clusters defined")
        return cat
    points = 0
    for c in clusters:
        if c.connect_timeout_seconds <= 5:
            points += 10
        else:
            cat.notes.append(f"{c.name}: connect_timeout > 5s")
        if c.hosts:
            points += 10
        else:
            cat.notes.append(f"{c.name}: no upstream hosts")
    cat.score = min(40, points)
    return cat


def _score_routes(listeners: List[ListenerConfig]) -> ScoreCategory:
    cat = ScoreCategory(name="Routes", score=0, max_score=30)
    routes = [r for ln in listeners for r in ln.routes]
    if not routes:
        cat.notes.append("No routes defined")
        return cat
    points = 0
    for r in routes:
        if r.retry_policy is not None:
            points += 10
        else:
            cat.notes.append(f"Route '{r.match_prefix}': no retry policy")
        if r.timeout_seconds and r.timeout_seconds <= 30:
            points += 5
        else:
            cat.notes.append(f"Route '{r.match_prefix}': missing or large timeout")
    cat.score = min(30, points)
    return cat


def _score_listeners(listeners: List[ListenerConfig]) -> ScoreCategory:
    cat = ScoreCategory(name="Listeners", score=0, max_score=30)
    if not listeners:
        cat.notes.append("No listeners defined")
        return cat
    points = 0
    for ln in listeners:
        if 1024 <= ln.port <= 65535:
            points += 15
        else:
            cat.notes.append(f"Listener '{ln.name}': unusual port {ln.port}")
        if ln.routes:
            points += 15
        else:
            cat.notes.append(f"Listener '{ln.name}': has no routes")
    cat.score = min(30, points)
    return cat


def score_config(listeners: List[ListenerConfig]) -> ScoreResult:
    """Return a ScoreResult for the given listener/route/cluster tree."""
    return ScoreResult(
        categories=[
            _score_listeners(listeners),
            _score_routes(listeners),
            _score_clusters(listeners),
        ]
    )
