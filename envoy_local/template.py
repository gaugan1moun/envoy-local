"""Template engine for generating Envoy config fragments from named presets."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


PRESETS: Dict[str, Dict[str, Any]] = {
    "http_default": {
        "connect_timeout": "0.25s",
        "lb_policy": "ROUND_ROBIN",
        "max_retries": 2,
        "retry_on": "5xx,connect-failure",
    },
    "grpc_default": {
        "connect_timeout": "0.5s",
        "lb_policy": "LEAST_REQUEST",
        "max_retries": 3,
        "retry_on": "5xx,reset,connect-failure",
    },
    "static_strict": {
        "connect_timeout": "1s",
        "lb_policy": "RANDOM",
        "max_retries": 0,
        "retry_on": "",
    },
}


class TemplateError(Exception):
    """Raised when a template preset is invalid or unknown."""


@dataclass
class TemplateResult:
    preset_name: str
    cluster_overrides: Dict[str, Any] = field(default_factory=dict)
    route_overrides: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "preset": self.preset_name,
            "cluster": self.cluster_overrides,
            "route": self.route_overrides,
        }


def list_presets() -> List[str]:
    """Return the names of all available presets."""
    return sorted(PRESETS.keys())


def apply_preset(preset_name: str, overrides: Optional[Dict[str, Any]] = None) -> TemplateResult:
    """Apply a named preset, optionally merging caller-supplied overrides.

    Args:
        preset_name: One of the keys in PRESETS.
        overrides: Optional dict whose values take precedence over the preset.

    Returns:
        A TemplateResult with cluster and route override dicts populated.

    Raises:
        TemplateError: If the preset name is unknown.
    """
    if preset_name not in PRESETS:
        raise TemplateError(
            f"Unknown preset '{preset_name}'. Available: {', '.join(list_presets())}"
        )

    base = dict(PRESETS[preset_name])
    if overrides:
        base.update(overrides)

    cluster_overrides = {
        "connect_timeout": base.get("connect_timeout", "0.25s"),
        "lb_policy": base.get("lb_policy", "ROUND_ROBIN"),
    }
    route_overrides: Dict[str, Any] = {}
    if base.get("max_retries", 0):
        route_overrides["retry_policy"] = {
            "retry_on": base.get("retry_on", "5xx"),
            "num_retries": base["max_retries"],
        }

    return TemplateResult(
        preset_name=preset_name,
        cluster_overrides=cluster_overrides,
        route_overrides=route_overrides,
    )
