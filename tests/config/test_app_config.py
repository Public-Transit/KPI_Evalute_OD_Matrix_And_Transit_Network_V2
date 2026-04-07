import json
from pathlib import Path
from uuid import uuid4

import pytest

from src.config.app_config import AppConfig, load_app_config


def _write_workspace_config(payload: dict) -> Path:
    config_dir = Path(__file__).resolve().parents[2] / ".test_tmp_config"
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / f"{uuid4()}.json"
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    return config_path


def test_app_config_loads_partial_json_and_keeps_defaults():
    config_path = _write_workspace_config(
        {
            "spatial_coverage": {"radius_m": 250.0},
            "od_aggregation": {"alpha": 0.85},
        }
    )

    try:
        config = AppConfig.load_from_file(config_path)

        assert config.spatial_coverage.radius_m == pytest.approx(250.0)
        assert config.od_aggregation.alpha == pytest.approx(0.85)
        assert config.composite_quality_index.transfer_weight == pytest.approx(0.45)
    finally:
        config_path.unlink(missing_ok=True)


def test_app_config_rejects_unknown_keys():
    with pytest.raises(ValueError, match="Unknown config keys"):
        AppConfig.from_dict({"spatial_coverage": {"radius_m": 500.0, "buffer": 100.0}})


def test_load_app_config_uses_environment_override(monkeypatch):
    config_path = _write_workspace_config(
        {"spatial_coverage": {"radius_m": 310.0}}
    )

    try:
        monkeypatch.setenv("KPI_APP_CONFIG_PATH", str(config_path))

        config = load_app_config()

        assert config.spatial_coverage.radius_m == pytest.approx(310.0)
    finally:
        config_path.unlink(missing_ok=True)
