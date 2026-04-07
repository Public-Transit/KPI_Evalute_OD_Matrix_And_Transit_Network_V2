# src/entrypoints/api.py
from numbers import Real
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.adapters.geospatial.geopy_shapely import ShapelyGeometryCalculator
from src.domain.service.filter import MinDistanceCandidateTripFilterV2
from src.domain.service.routing import CombinedRoutingEngine
from src.domain.service.trip_kpi_caculator.total_potential_demand_in_trip import (
    TotalPotentialDemandInTripCalculator,
)

from src.adapters.repository.fake_repo_grid_3x3 import FakeRepoGrid3x3

from src.service_layer.service.route_kpi_service import calculate_kpis_for_all_routes
from src.service_layer.unit_of_work import DummyUnitOfWork

app = FastAPI(
    title="Transit Network KPI API",
    description="API dinh tuyen va danh gia KPI mang luoi giao thong",
)

@app.get("/")
def read_root():
    return {"message": "Server is running"}

@app.post(
    "/api/kpi/calculate-all-routes",
)
def calculate_kpi_all_routes():
    """
    Calculate concise route-level KPI results for all routes.
    """
    repo = FakeRepoGrid3x3()
    uow = DummyUnitOfWork(repo)
    routing_engine = CombinedRoutingEngine()
    filter_engine = MinDistanceCandidateTripFilterV2()
    geo_calc = ShapelyGeometryCalculator()

    try:
        results = calculate_kpis_for_all_routes(
            [TotalPotentialDemandInTripCalculator()],
            uow,
            routing_engine,
            geo_calc,
            "fake_path"
        )
        return {"status": "success", "data": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
