from typing import Dict, Any
from backend.app.config import get_settings

class CostAndCarbonEngine:
    def __init__(self):
        self.settings = get_settings()

    def compute_instantaneous_metrics(self, power_w: float, carbon_intensity_g_kwh: float, tariff_inr_kwh: float = None) -> Dict[str, float]:
        """
        Computes hourly burn rates for cost (INR/hr) and emissions (gCO2/hr)
        based on active power draw in Watts.
        """
        effective_tariff = tariff_inr_kwh if tariff_inr_kwh is not None else self.settings.DEFAULT_TARIFF_INR_PER_KWH
        kw = power_w / 1000.0

        cost_rate_inr_hr = round(kw * effective_tariff, 4)
        carbon_rate_g_hr = round(kw * carbon_intensity_g_kwh, 2)

        return {
            "power_kw": round(kw, 4),
            "tariff_inr_per_kwh": effective_tariff,
            "cost_rate_inr_hr": cost_rate_inr_hr,
            "carbon_rate_g_hr": carbon_rate_g_hr
        }

    def compute_energy_cost(self, energy_kwh: float, tariff_inr_kwh: float = None) -> float:
        """
        Computes total monetary cost for cumulative energy in kWh.
        """
        effective_tariff = tariff_inr_kwh if tariff_inr_kwh is not None else self.settings.DEFAULT_TARIFF_INR_PER_KWH
        return round(energy_kwh * effective_tariff, 2)

    def compute_energy_carbon(self, energy_kwh: float, carbon_intensity_g_kwh: float) -> float:
        """
        Computes total associated carbon footprint in grams CO2e for cumulative energy.
        """
        return round(energy_kwh * carbon_intensity_g_kwh, 2)

cost_engine = CostAndCarbonEngine()
