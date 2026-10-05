from backend.app.config import get_settings
from backend.app.models.schemas import PowerTelemetryRequest, HostTelemetryRequest, GridCarbonRequest
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from collections import deque

logger = logging.getLogger(__name__)

# Optional import of influxdb_client with fallback
try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUX_AVAILABLE = True
except ImportError:
    INFLUX_AVAILABLE = False
    logger.warning("influxdb_client library not installed. Operating in in-memory fallback mode.")

class InfluxService:
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.write_api = None
        self.query_api = None
        
        # In-memory buffer for local testing when InfluxDB daemon is not running
        self._memory_power_buffer: deque = deque(maxlen=200)
        self._memory_host_buffer: deque = deque(maxlen=200)
        self._memory_grid_buffer: deque = deque(maxlen=200)

        if INFLUX_AVAILABLE:
            self._connect()

    def _connect(self):
        if not INFLUX_AVAILABLE:
            return
        try:
            self.client = InfluxDBClient(
                url=self.settings.INFLUXDB_URL,
                token=self.settings.INFLUXDB_TOKEN,
                org=self.settings.INFLUXDB_ORG,
                timeout=5_000
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            logger.info("Connected to InfluxDB at %s (Org: %s)", self.settings.INFLUXDB_URL, self.settings.INFLUXDB_ORG)
        except Exception as e:
            logger.warning("Could not establish connection to InfluxDB (%s). Using in-memory fallback.", str(e))
            self.client = None

    def is_healthy(self) -> bool:
        if not INFLUX_AVAILABLE or not self.client:
            return False
        try:
            health = self.client.health()
            return health.status == "pass"
        except Exception:
            return False

    def write_power_telemetry(self, data: PowerTelemetryRequest) -> bool:
        record_dict = data.model_dump()
        record_dict["time"] = (data.timestamp or datetime.now(timezone.utc)).isoformat()
        self._memory_power_buffer.append(record_dict)

        if not INFLUX_AVAILABLE or not self.write_api:
            return True

        try:
            point = (
                Point("power_consumption")
                .tag("device_id", data.device_id)
                .tag("source", data.source)
                .field("voltage_v", float(data.voltage_v))
                .field("current_a", float(data.current_a))
                .field("power_w", float(data.power_w))
                .field("energy_kwh", float(data.energy_kwh or 0.0))
                .field("power_factor", float(data.power_factor or 1.0))
                .field("frequency_hz", float(data.frequency_hz or 50.0))
                .time(data.timestamp or datetime.now(timezone.utc), WritePrecision.MS)
            )
            self.write_api.write(bucket=self.settings.INFLUXDB_BUCKET, org=self.settings.INFLUXDB_ORG, record=point)
            return True
        except Exception as e:
            logger.debug("InfluxDB write bypassed/errored: %s (saved in memory)", str(e))
            return True

    def write_host_telemetry(self, data: HostTelemetryRequest) -> bool:
        record_dict = data.model_dump()
        record_dict["time"] = (data.timestamp or datetime.now(timezone.utc)).isoformat()
        self._memory_host_buffer.append(record_dict)

        if not INFLUX_AVAILABLE or not self.write_api:
            return True

        try:
            point = (
                Point("host_telemetry")
                .tag("node_id", data.node_id)
                .field("cpu_percent", float(data.cpu_percent))
                .field("memory_percent", float(data.memory_percent))
                .field("disk_io_read_mbps", float(data.disk_io_read_mbps or 0.0))
                .field("disk_io_write_mbps", float(data.disk_io_write_mbps or 0.0))
                .field("net_io_rx_mbps", float(data.net_io_rx_mbps or 0.0))
                .field("net_io_tx_mbps", float(data.net_io_tx_mbps or 0.0))
                .time(data.timestamp or datetime.now(timezone.utc), WritePrecision.MS)
            )
            if data.temperature_c is not None:
                point.field("temperature_c", float(data.temperature_c))

            self.write_api.write(bucket=self.settings.INFLUXDB_BUCKET, org=self.settings.INFLUXDB_ORG, record=point)
            return True
        except Exception as e:
            logger.debug("InfluxDB host write bypassed: %s", str(e))
            return True

    def write_grid_carbon(self, data: GridCarbonRequest) -> bool:
        record_dict = data.model_dump()
        record_dict["time"] = (data.timestamp or datetime.now(timezone.utc)).isoformat()
        self._memory_grid_buffer.append(record_dict)

        if not INFLUX_AVAILABLE or not self.write_api:
            return True

        try:
            point = (
                Point("grid_carbon")
                .tag("zone", data.zone)
                .field("carbon_intensity_g_co2_kwh", float(data.carbon_intensity_g_co2_kwh))
                .field("tariff_inr_per_kwh", float(data.electricity_tariff_inr_per_kwh or 11.50))
                .time(data.timestamp or datetime.now(timezone.utc), WritePrecision.MS)
            )
            self.write_api.write(bucket=self.settings.INFLUXDB_BUCKET, org=self.settings.INFLUXDB_ORG, record=point)
            return True
        except Exception as e:
            logger.debug("InfluxDB grid write bypassed: %s", str(e))
            return True

    def get_latest_power(self, device_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        # Check InfluxDB query first
        if INFLUX_AVAILABLE and self.query_api:
            try:
                device_filter = f'|> filter(fn: (r) => r.device_id == "{device_id}")' if device_id else ""
                query = f'''
                    from(bucket: "{self.settings.INFLUXDB_BUCKET}")
                    |> range(start: -15m)
                    |> filter(fn: (r) => r._measurement == "power_consumption")
                    {device_filter}
                    |> last()
                '''
                result = self.query_api.query(query=query, org=self.settings.INFLUXDB_ORG)
                data: Dict[str, Any] = {}
                for table in result:
                    for record in table.records:
                        data[record.get_field()] = record.get_value()
                        data["time"] = record.get_time().isoformat()
                        data["device_id"] = record.values.get("device_id")
                if data:
                    return data
            except Exception as e:
                logger.debug("InfluxDB query failed, checking memory buffer: %s", str(e))

        # In-memory buffer fallback
        if self._memory_power_buffer:
            if device_id:
                for reading in reversed(self._memory_power_buffer):
                    if reading.get("device_id") == device_id:
                        return reading
            return self._memory_power_buffer[-1]
        return None

influx_service = InfluxService()
