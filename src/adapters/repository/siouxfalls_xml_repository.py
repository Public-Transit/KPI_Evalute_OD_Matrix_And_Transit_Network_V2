from __future__ import annotations

from pathlib import Path

from src.adapters.repository.cottbus_xml_repository import CottbusXmlRepository


class SiouxFallsXmlRepository(CottbusXmlRepository):
    """
    XML repository preset for Sioux Falls MATSim inputs.

    Reuses the same parsing logic as Cottbus because both datasets follow
    transit schedule + population XML structure.
    """

    def __init__(
        self,
        data_dir: str | Path = "siouxfalls",
        schedule_file: str = "Siouxfalls_transitSchedule.xml",
        plans_file: str = "Siouxfalls_population.xml",
        max_plans: int | None = 200,
        grid_cell_size_m: float = 500.0,
        default_demand: float = 1.0,
        source_crs: str = "EPSG:32614",
        target_crs: str = "EPSG:4326",
    ):
        super().__init__(
            data_dir=data_dir,
            schedule_file=schedule_file,
            plans_file=plans_file,
            max_plans=max_plans,
            grid_cell_size_m=grid_cell_size_m,
            default_demand=default_demand,
            source_crs=source_crs,
            target_crs=target_crs,
        )
