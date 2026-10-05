from fastapi import APIRouter, HTTPException, Query
from backend.app.models.schemas import (
    PowerTelemetryRequest,
    HostTelemetryRequest,
    GridCarbonRequest,
    TelemetryIngestResponse
)
from backend.app.services.influx_service import influx_service
from backend.app.services.carbon_service import carbon_service
from backend.app.services.cost_engine import cost_engine
from typing import Optional, Dict, Any
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry Ingestion"])

@router.post("/power", response_model=TelemetryIngestResponse)
def ingest_power_telemetry(payload: PowerTelemetryRequest):
    """
    Ingests live power telemetry from PZEM-004T, Smart Plug, IPMI, or Mock Agent.
    """
    success = influx_service.write_power_telemetry(payload)
    if not success:
        # Still return 200/accepted in development or log warning if DB is warming up
        return TelemetryIngestResponse(
            status="accepted_with_db_warning",
            message="Telemetry parsed successfully, but InfluxDB write pending or offline.",
            points_written=0
        )
    return TelemetryIngestResponse(
        status="success",
        message=f"Power reading for device '{payload.device_id}' written successfully.",
        points_written=1
    )

@router.post("/host", response_model=TelemetryIngestResponse)
def ingest_host_telemetry(payload: HostTelemetryRequest):
    """
    Ingests compute metrics (CPU, RAM, disk, network) from local host daemon or college server.
    """
    success = influx_service.write_host_telemetry(payload)
    if not success:
        return TelemetryIngestResponse(
            status="accepted_with_db_warning",
            message="Host telemetry parsed, but InfluxDB write pending.",
            points_written=0
        )
    return TelemetryIngestResponse(
        status="success",
        message=f"Host telemetry for node '{payload.node_id}' written successfully.",
        points_written=1
    )

@router.post("/grid", response_model=TelemetryIngestResponse)
def ingest_grid_telemetry(payload: GridCarbonRequest):
    """
    Ingests carbon intensity and tariff updates.
    """
    success = influx_service.write_grid_carbon(payload)
    return TelemetryIngestResponse(
        status="success" if success else "accepted_with_db_warning",
        message=f"Grid reading for zone '{payload.zone}' processed.",
        points_written=1 if success else 0
    )

@router.get("/grid/current", response_model=GridCarbonRequest)
def get_current_grid_conditions():
    """
    Returns latest grid carbon intensity and tariff.
    """
    return carbon_service.get_current_grid_carbon()

@router.get("/latest")
def get_latest_telemetry(device_id: Optional[str] = Query(default=None)):
    """
    Returns latest aggregated telemetry snapshot (Power + Grid Carbon + Cost calculation).
    """
    power_data = influx_service.get_latest_power(device_id)
    grid_data = carbon_service.get_current_grid_carbon()

    power_w = float(power_data.get("power_w", 0.0)) if power_data else 0.0
    energy_kwh = float(power_data.get("energy_kwh", 0.0)) if power_data else 0.0

    cost_metrics = cost_engine.compute_instantaneous_metrics(
        power_w=power_w,
        carbon_intensity_g_kwh=grid_data.carbon_intensity_g_co2_kwh,
        tariff_inr_kwh=grid_data.electricity_tariff_inr_per_kwh
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "power_telemetry": power_data,
        "grid_telemetry": grid_data.model_dump(),
        "burn_rates": cost_metrics,
        "cumulative_cost_inr": cost_engine.compute_energy_cost(energy_kwh, grid_data.electricity_tariff_inr_per_kwh),
        "cumulative_carbon_g_co2": cost_engine.compute_energy_carbon(energy_kwh, grid_data.carbon_intensity_g_co2_kwh)
    }
