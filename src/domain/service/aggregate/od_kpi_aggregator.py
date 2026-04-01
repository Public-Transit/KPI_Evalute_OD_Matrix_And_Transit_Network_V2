from __future__ import annotations

from collections.abc import Mapping
from numbers import Real
from typing import Any


class ODKPIAggregator:
    SCORE_SCALE = "0_100_higher_is_better"
    NO_VALID_TRIPS_REASON = "No valid trips after hard-threshold filtering"

    def calculate(
        self,
        trip_kpi_results: list[dict],
        *,
        alpha: float = 0.7,
        max_valid_transfer_count: float = 1.0,
        max_valid_circuity: float = 2.5,
        min_valid_service_coverage_ratio: float = 0.1,
    ) -> dict[str, Any]:
        self._validate_configuration(
            alpha=alpha,
            max_valid_transfer_count=max_valid_transfer_count,
            max_valid_circuity=max_valid_circuity,
            min_valid_service_coverage_ratio=min_valid_service_coverage_ratio,
        )

        valid_trip_scores = []
        for trip_kpi_result in trip_kpi_results:
            extracted_trip_scores = self._extract_valid_trip_scores(
                trip_kpi_result,
                max_valid_transfer_count=max_valid_transfer_count,
                max_valid_circuity=max_valid_circuity,
                min_valid_service_coverage_ratio=min_valid_service_coverage_ratio,
            )
            if extracted_trip_scores is not None:
                valid_trip_scores.append(extracted_trip_scores)

        if not valid_trip_scores:
            return {
                "transfer_kpi": self._build_invalid_metric_result(alpha),
                "circuity_kpi": self._build_invalid_metric_result(alpha),
                "spatial_coverage_kpi": self._build_invalid_metric_result(alpha),
                "composite_kpi": self._build_invalid_metric_result(alpha),
            }

        return {
            "transfer_kpi": self._aggregate_metric(
                [trip_score["transfer_score"] for trip_score in valid_trip_scores],
                alpha=alpha,
            ),
            "circuity_kpi": self._aggregate_metric(
                [trip_score["circuity_score"] for trip_score in valid_trip_scores],
                alpha=alpha,
            ),
            "spatial_coverage_kpi": self._aggregate_metric(
                [trip_score["service_coverage_score"] for trip_score in valid_trip_scores],
                alpha=alpha,
            ),
            "composite_kpi": self._aggregate_metric(
                [trip_score["composite_score"] for trip_score in valid_trip_scores],
                alpha=alpha,
            ),
        }

    def _validate_configuration(
        self,
        *,
        alpha: float,
        max_valid_transfer_count: float,
        max_valid_circuity: float,
        min_valid_service_coverage_ratio: float,
    ) -> None:
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("'alpha' must be between 0 and 1")
        if max_valid_transfer_count < 0.0:
            raise ValueError("'max_valid_transfer_count' must be >= 0")
        if max_valid_circuity <= 0.0:
            raise ValueError("'max_valid_circuity' must be > 0")
        if min_valid_service_coverage_ratio < 0.0:
            raise ValueError("'min_valid_service_coverage_ratio' must be >= 0")

    def _extract_valid_trip_scores(
        self,
        trip_kpi_result: dict[str, Any],
        *,
        max_valid_transfer_count: float,
        max_valid_circuity: float,
        min_valid_service_coverage_ratio: float,
    ) -> dict[str, float] | None:
        if not isinstance(trip_kpi_result, Mapping):
            return None

        transfer_raw = self._coerce_numeric(
            self._deep_get(trip_kpi_result, "transfer_kpi", "score")
        )
        circuity_raw = self._coerce_numeric(
            self._deep_get(trip_kpi_result, "circuity_kpi", "score")
        )
        service_coverage_raw = self._coerce_numeric(
            self._deep_get(trip_kpi_result, "spatial_coverage_kpi", "score_ratio")
        )
        composite_score = self._coerce_numeric(
            self._deep_get(trip_kpi_result, "composite_kpi", "score")
        )
        transfer_score = self._coerce_numeric(
            self._deep_get(trip_kpi_result, "composite_kpi", "normalized_scores", "transfer")
        )
        circuity_score = self._coerce_numeric(
            self._deep_get(trip_kpi_result, "composite_kpi", "normalized_scores", "circuity")
        )
        service_coverage_score = self._coerce_numeric(
            self._deep_get(
                trip_kpi_result, "composite_kpi", "normalized_scores", "service_coverage"
            )
        )

        if (
            transfer_raw is None
            or circuity_raw is None
            or service_coverage_raw is None
            or composite_score is None
            or transfer_score is None
            or circuity_score is None
            or service_coverage_score is None
        ):
            return None

        if transfer_raw > max_valid_transfer_count:
            return None
        if circuity_raw > max_valid_circuity:
            return None
        if service_coverage_raw < min_valid_service_coverage_ratio:
            return None

        return {
            "transfer_score": transfer_score,
            "circuity_score": circuity_score,
            "service_coverage_score": service_coverage_score,
            "composite_score": composite_score,
        }

    def _aggregate_metric(self, scores: list[float], *, alpha: float) -> dict[str, Any]:
        best_score = max(scores)
        weights = self._calculate_rank_weights(scores)
        weighted_average_score = sum(weight * score for weight, score in zip(weights, scores)) / sum(
            weights
        )
        od_score = alpha * best_score + (1.0 - alpha) * weighted_average_score

        return {
            "score": od_score,
            "score_scale": self.SCORE_SCALE,
            "is_valid": True,
            "reason": None,
            "best_score": best_score,
            "weighted_average_score": weighted_average_score,
            "parameters": {
                "alpha": alpha,
            },
        }

    def _calculate_rank_weights(self, scores: list[float]) -> list[float]:
        indexed_scores = list(enumerate(scores))
        sorted_scores = sorted(indexed_scores, key=lambda item: item[1], reverse=True)
        total_scores = len(sorted_scores)
        weights = [0.0] * total_scores

        position = 1
        index = 0
        while index < total_scores:
            tie_end_index = index + 1
            while tie_end_index < total_scores and sorted_scores[tie_end_index][1] == sorted_scores[index][1]:
                tie_end_index += 1

            last_position = position + (tie_end_index - index) - 1
            average_rank = (position + last_position) / 2.0
            weight = (total_scores - average_rank + 1.0) / total_scores

            for tied_index in range(index, tie_end_index):
                original_index, _ = sorted_scores[tied_index]
                weights[original_index] = weight

            position = last_position + 1
            index = tie_end_index

        return weights

    def _build_invalid_metric_result(self, alpha: float) -> dict[str, Any]:
        return {
            "score": None,
            "score_scale": self.SCORE_SCALE,
            "is_valid": False,
            "reason": self.NO_VALID_TRIPS_REASON,
            "best_score": None,
            "weighted_average_score": None,
            "parameters": {
                "alpha": alpha,
            },
        }

    def _coerce_numeric(self, value: Any) -> float | None:
        if value is None:
            return None

        if isinstance(value, str):
            stripped_value = value.strip()
            try:
                return float(stripped_value)
            except ValueError:
                return None

        if isinstance(value, bool) or not isinstance(value, Real):
            return None

        return float(value)

    def _deep_get(self, data: Mapping[str, Any], *keys: str) -> Any:
        current_value: Any = data
        for key in keys:
            if not isinstance(current_value, Mapping):
                return None
            current_value = current_value.get(key)
        return current_value
