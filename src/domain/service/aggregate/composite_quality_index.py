from __future__ import annotations

from numbers import Real
from typing import Any

from src.config.app_config import CompositeQualityIndexConfig


class CompositeQualityIndexCalculator:
    """
    Aggregate three KPI scores into a composite quality index on a 0-100 scale.

    Inputs are raw KPI values:
    - transfer_score: number of transfers
    - circuity_score: circuity index
    - service_coverage_ratio: coverage ratio in the range [0, 1]
    """

    INVALID_MARKERS = {"Not valid", "Not valid or >1"}

    def __init__(self, config: CompositeQualityIndexConfig | None = None):
        self._config = config or CompositeQualityIndexConfig()

    def calculate(
        self,
        transfer_score: Any,
        circuity_score: Any,
        service_coverage_ratio: Any,
        *,
        transfer_max: float | None = None,
        circuity_max: float | None = None,
        transfer_weight: float | None = None,
        circuity_weight: float | None = None,
        service_coverage_weight: float | None = None,
    ) -> dict[str, Any]:
        transfer_max = self._config.transfer_max if transfer_max is None else transfer_max
        circuity_max = self._config.circuity_max if circuity_max is None else circuity_max
        transfer_weight = self._config.transfer_weight if transfer_weight is None else transfer_weight
        circuity_weight = self._config.circuity_weight if circuity_weight is None else circuity_weight
        service_coverage_weight = (
            self._config.service_coverage_weight
            if service_coverage_weight is None
            else service_coverage_weight
        )

        if transfer_max <= 0:
            raise ValueError("'transfer_max' must be greater than 0")
        if circuity_max <= 1:
            raise ValueError("'circuity_max' must be greater than 1")

        raw_inputs = {
            "transfer_count": transfer_score,
            "circuity_index": circuity_score,
            "service_coverage_ratio": service_coverage_ratio,
        }

        invalid_inputs: dict[str, str] = {}

        transfer_value = self._coerce_numeric(transfer_score, "transfer_count", invalid_inputs)
        circuity_value = self._coerce_numeric(circuity_score, "circuity_index", invalid_inputs)
        service_coverage_value = self._coerce_numeric(
            service_coverage_ratio, "service_coverage_ratio", invalid_inputs
        )

        normalized_scores = {
            "transfer": None,
            "circuity": None,
            "service_coverage": None,
        }
        weighted_scores = {
            "transfer": None,
            "circuity": None,
            "service_coverage": None,
        }

        if transfer_value is not None:
            normalized_scores["transfer"] = self._clamp(
                100.0 * (1.0 - (transfer_value / transfer_max)), 0.0, 100.0
            )
            weighted_scores["transfer"] = transfer_weight * normalized_scores["transfer"]

        if circuity_value is not None:
            normalized_scores["circuity"] = self._clamp(
                100.0 * ((circuity_max - circuity_value) / (circuity_max - 1.0)),
                0.0,
                100.0,
            )
            weighted_scores["circuity"] = circuity_weight * normalized_scores["circuity"]

        if service_coverage_value is not None:
            normalized_scores["service_coverage"] = self._clamp(
                service_coverage_value * 100.0, 0.0, 100.0
            )
            weighted_scores["service_coverage"] = (
                service_coverage_weight * normalized_scores["service_coverage"]
            )

        is_valid = not invalid_inputs
        reason = None
        score = None

        if is_valid:
            score = (
                weighted_scores["transfer"]
                + weighted_scores["circuity"]
                + weighted_scores["service_coverage"]
            )
        else:
            reason = "Composite KPI cannot be calculated because one or more inputs are invalid."

        return {
            "score": score,
            "is_valid": is_valid,
            "reason": reason,
            "invalid_inputs": invalid_inputs,
            "raw_inputs": raw_inputs,
            "normalized_scores": normalized_scores,
            "weights": {
                "transfer": transfer_weight,
                "circuity": circuity_weight,
                "service_coverage": service_coverage_weight,
            },
            "weighted_scores": weighted_scores,
            "parameters": {
                "transfer_max": transfer_max,
                "circuity_max": circuity_max,
            },
        }

    def _coerce_numeric(
        self, value: Any, field_name: str, invalid_inputs: dict[str, str]
    ) -> float | None:
        if value is None:
            invalid_inputs[field_name] = "Value is None"
            return None

        if isinstance(value, str):
            stripped_value = value.strip()
            if stripped_value in self.INVALID_MARKERS:
                invalid_inputs[field_name] = f"Invalid KPI marker: {stripped_value}"
                return None
            try:
                return float(stripped_value)
            except ValueError:
                invalid_inputs[field_name] = f"Expected numeric value, got: {value}"
                return None

        if isinstance(value, bool) or not isinstance(value, Real):
            invalid_inputs[field_name] = f"Expected numeric value, got: {type(value).__name__}"
            return None

        return float(value)

    @staticmethod
    def _clamp(value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(maximum, value))
