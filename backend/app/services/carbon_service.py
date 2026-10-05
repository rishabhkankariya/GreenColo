import requests
import logging
from datetime import datetime, timezone
import random
from typing import Dict, Any, Optional
from backend.app.config import get_settings
from backend.app.models.schemas import GridCarbonRequest

logger = logging.getLogger(__name__)

class CarbonService:
    def __init__(self):
        self.settings = get_settings()
        self.last_known_reading: Optional[GridCarbonRequest] = None

    def get_current_grid_carbon(self) -> GridCarbonRequest:
        """
        Polls Electricity Maps API if API key is provided and mock mode is off.
        Otherwise provides a realistic fluctuating carbon intensity for zone IN-WE (Maharashtra/Western India).
        """
        if not self.settings.USE_MOCK_CARBON and self.settings.ELECTRICITY_MAPS_API_KEY:
            try:
                url = f"https://api.electricitymaps.com/v3/carbon-intensity/latest?zone={self.settings.ELECTRICITY_MAPS_ZONE}"
                headers = {"auth-token": self.settings.ELECTRICITY_MAPS_API_KEY}
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    reading = GridCarbonRequest(
                        timestamp=datetime.now(timezone.utc),
                        zone=self.settings.ELECTRICITY_MAPS_ZONE,
                        carbon_intensity_g_co2_kwh=float(data.get("carbonIntensity", 650.0)),
                        electricity_tariff_inr_per_kwh=self.settings.DEFAULT_TARIFF_INR_PER_KWH
                    )
                    self.last_known_reading = reading
                    return reading
                else:
                    logger.warning("Electricity Maps API returned status %d. Falling back to cached/mock.", response.status_code)
            except Exception as e:
                logger.error("Electricity Maps API request error: %s. Using fallback.", str(e))

        # Mock / Fallback generation for Maharashtra (IN-WE)
        # Western India grid is predominantly coal/thermal (~70-80%) with seasonal renewables, typical intensity: 620 - 720 gCO2/kWh
        base_intensity = 660.0
        jitter = random.uniform(-30.0, 30.0)
        simulated_intensity = round(base_intensity + jitter, 1)

        simulated_fossil = round(random.uniform(74.0, 82.0), 1)
        simulated_renewable = round(100.0 - simulated_fossil, 1)

        reading = GridCarbonRequest(
            timestamp=datetime.now(timezone.utc),
            zone=self.settings.ELECTRICITY_MAPS_ZONE,
            carbon_intensity_g_co2_kwh=simulated_intensity,
            fossil_fuel_percentage=simulated_fossil,
            renewable_percentage=simulated_renewable,
            electricity_tariff_inr_per_kwh=self.settings.DEFAULT_TARIFF_INR_PER_KWH
        )
        self.last_known_reading = reading
        return reading

carbon_service = CarbonService()
