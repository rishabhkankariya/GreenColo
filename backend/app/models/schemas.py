from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

class PowerTelemetryRequest(BaseModel):
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    device_id: str = Field(..., description="Unique ID of measuring sensor or device")
    source: str = Field(default="pzem-004t", description="Hardware source: pzem-004t, smart_plug, ipmi, or mock")
    voltage_v: float = Field(..., ge=0.0, description="Measured RMS voltage in Volts")
    current_a: float = Field(..., ge=0.0, description="Measured RMS current in Amperes")
    power_w: float = Field(..., ge=0.0, description="Active real power in Watts")
    energy_kwh: Optional[float] = Field(default=0.0, ge=0.0, description="Accumulated energy in kWh")
    power_factor: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Power factor (0.0 to 1.0)")
    frequency_hz: Optional[float] = Field(default=50.0, ge=40.0, le=70.0, description="AC Grid frequency in Hz")

class HostTelemetryRequest(BaseModel):
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    node_id: str = Field(..., description="Identifier of host node / PC / server")
    cpu_percent: float = Field(..., ge=0.0, le=100.0, description="Total CPU utilization percentage")
    memory_percent: float = Field(..., ge=0.0, le=100.0, description="Total RAM utilization percentage")
    disk_io_read_mbps: Optional[float] = Field(default=0.0, ge=0.0)
    disk_io_write_mbps: Optional[float] = Field(default=0.0, ge=0.0)
    net_io_rx_mbps: Optional[float] = Field(default=0.0, ge=0.0)
    net_io_tx_mbps: Optional[float] = Field(default=0.0, ge=0.0)
    temperature_c: Optional[float] = Field(default=None, description="CPU package or ambient temperature in C")

class GridCarbonRequest(BaseModel):
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    zone: str = Field(default="IN-WE", description="Electricity Maps grid zone identifier")
    carbon_intensity_g_co2_kwh: float = Field(..., ge=0.0, description="Grid carbon intensity in gCO2eq/kWh")
    fossil_fuel_percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    renewable_percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    electricity_tariff_inr_per_kwh: Optional[float] = Field(default=11.50, ge=0.0)

class TelemetryIngestResponse(BaseModel):
    status: str = "success"
    message: str
    points_written: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DecisionRequest(BaseModel):
    workload_id: str = Field(..., description="Unique identifier for the incoming job")
    name: str = Field(..., description="Human-readable workload name")
    workload_type: str = Field(default="batch", description="batch, web_service, or ml_training")
    cpu_cores_required: float = Field(default=1.0, ge=0.1)
    memory_mb_required: int = Field(default=1024, ge=128)
    deadline_minutes: Optional[int] = Field(default=60, ge=1)
    latency_tolerance: str = Field(default="high", description="low, medium, or high")
    sustainability_priority: float = Field(default=0.6, ge=0.0, le=1.0)
    cost_priority: float = Field(default=0.4, ge=0.0, le=1.0)

class DecisionResponse(BaseModel):
    decision_id: str
    workload_id: str
    timestamp: datetime
    recommended_destination: str = Field(..., description="ON_PREMISE or AWS_CLOUD")
    reason: str
    scores: Dict[str, float]
    estimated_power_w: float
    estimated_carbon_g_co2: float
    estimated_cost_inr: float
    sla_feasible: bool
