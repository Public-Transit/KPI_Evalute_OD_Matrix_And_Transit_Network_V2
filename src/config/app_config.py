from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_APP_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "app_config.json"
APP_CONFIG_PATH_ENV_VAR = "KPI_APP_CONFIG_PATH"


def _ensure_mapping(value: Any, section_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Section '{section_name}' must be a JSON object")
    return value


def _reject_unknown_keys(
    section_name: str,
    payload: dict[str, Any],
    allowed_keys: set[str],
) -> None:
    unknown_keys = sorted(set(payload) - allowed_keys)
    if unknown_keys:
        unknown_list = ", ".join(unknown_keys)
        raise ValueError(f"Unknown config keys in section '{section_name}': {unknown_list}")


@dataclass(frozen=True)
class SpatialCoverageConfig:
    radius_m: float = 500.0


@dataclass(frozen=True)
class CompositeQualityIndexConfig:
    transfer_max: float = 3.0
    circuity_max: float = 2.5
    transfer_weight: float = 0.45
    circuity_weight: float = 0.20
    service_coverage_weight: float = 0.35


@dataclass(frozen=True)
class ODAggregationConfig:
    alpha: float = 0.7
    max_valid_transfer_count: float = 1.0
    max_valid_circuity: float = 2.5
    min_valid_service_coverage_ratio: float = 0.0


@dataclass(frozen=True)
class AppConfig:
    spatial_coverage: SpatialCoverageConfig = field(default_factory=SpatialCoverageConfig)
    composite_quality_index: CompositeQualityIndexConfig = field(
        default_factory=CompositeQualityIndexConfig
    )
    od_aggregation: ODAggregationConfig = field(default_factory=ODAggregationConfig)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> AppConfig:
        root_payload = _ensure_mapping(payload, "root")
        _reject_unknown_keys(
            "root",
            root_payload,
            {
                "spatial_coverage",
                "composite_quality_index",
                "od_aggregation",
            },
        )

        spatial_coverage_payload = _ensure_mapping(
            root_payload.get("spatial_coverage"),
            "spatial_coverage",
        )
        _reject_unknown_keys(
            "spatial_coverage",
            spatial_coverage_payload,
            {"radius_m"},
        )

        composite_payload = _ensure_mapping(
            root_payload.get("composite_quality_index"),
            "composite_quality_index",
        )
        _reject_unknown_keys(
            "composite_quality_index",
            composite_payload,
            {
                "transfer_max",
                "circuity_max",
                "transfer_weight",
                "circuity_weight",
                "service_coverage_weight",
            },
        )

        aggregation_payload = _ensure_mapping(
            root_payload.get("od_aggregation"),
            "od_aggregation",
        )
        _reject_unknown_keys(
            "od_aggregation",
            aggregation_payload,
            {
                "alpha",
                "max_valid_transfer_count",
                "max_valid_circuity",
                "min_valid_service_coverage_ratio",
            },
        )

        return cls(
            spatial_coverage=SpatialCoverageConfig(**spatial_coverage_payload),
            composite_quality_index=CompositeQualityIndexConfig(**composite_payload),
            od_aggregation=ODAggregationConfig(**aggregation_payload),
        )

    @classmethod
    def load_from_file(cls, config_path: str | Path | None = None) -> AppConfig:
        explicit_path = config_path is not None
        resolved_path = Path(config_path).expanduser() if config_path else DEFAULT_APP_CONFIG_PATH

        if not resolved_path.exists():
            if explicit_path:
                raise FileNotFoundError(f"Config file not found: {resolved_path}")
            return cls()

        with resolved_path.open("r", encoding="utf-8") as config_file:
            payload = json.load(config_file)

        return cls.from_dict(payload)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_app_config(config_path: str | Path | None = None) -> AppConfig:
    resolved_path = config_path
    if resolved_path is None:
        env_path = os.getenv(APP_CONFIG_PATH_ENV_VAR)
        if env_path:
            resolved_path = env_path
    return AppConfig.load_from_file(resolved_path)
