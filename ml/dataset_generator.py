#!/usr/bin/env python3
"""
GreenColo: Telemetry & PUE Dataset Generator
Generates synthetic and recorded multi-variate time-series datasets
for training the XGBoost PUE and Workload Demand prediction engine.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import argparse
import os

def generate_telemetry_dataset(num_samples: int = 5000, output_path: str = "ml/data/telemetry_dataset.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    start_time = datetime.now(timezone.utc) - timedelta(minutes=num_samples * 2)
    timestamps = [start_time + timedelta(minutes=2 * i) for i in range(num_samples)]

    hours = [t.hour for t in timestamps]
    day_of_week = [t.weekday() for t in timestamps]

    # Daily diurnal cycle pattern for workload load (higher during 9am - 6pm)
    diurnal_curve = [np.sin((h - 6) / 24.0 * 2 * np.pi) for h in hours]
    
    # Base CPU load with diurnal shift + noise
    cpu_percent = np.clip(
        30.0 + (np.array(diurnal_curve) * 25.0) + np.random.normal(0, 10, num_samples),
        5.0, 98.0
    )

    # Memory utilization loosely correlates with CPU
    memory_percent = np.clip(
        40.0 + (cpu_percent * 0.35) + np.random.normal(0, 5, num_samples),
        15.0, 95.0
    )

    # Ambient / Server rack temperature (C)
    ambient_temp = 22.0 + (np.array(diurnal_curve) * 4.0) + np.random.normal(0, 0.8, num_samples)

    # Power consumption in Watts: Base server idle power (~120W) + dynamic CPU power + cooling overhead
    # P_it = P_idle + (P_max - P_idle) * (cpu / 100)
    it_power_w = 120.0 + (320.0 * (cpu_percent / 100.0)) + np.random.normal(0, 8, num_samples)

    # Total facility power includes cooling, UPS losses, lighting:
    # Cooling power scales with ambient temperature and IT heat load
    cooling_factor = 0.25 + (0.015 * (ambient_temp - 20.0))
    total_facility_power_w = it_power_w * (1.0 + cooling_factor) + np.random.normal(0, 12, num_samples)

    # PUE = Total Facility Power / IT Equipment Power
    # Target PUE range for modern hybrid/colocation: 1.15 to 1.65
    pue = np.clip(total_facility_power_w / it_power_w, 1.10, 1.85)

    # Grid carbon intensity (gCO2/kWh) - Western India / Maharashtra baseline ~620-720
    grid_carbon = np.clip(660.0 + (np.array(diurnal_curve) * 40.0) + np.random.normal(0, 20, num_samples), 450.0, 850.0)

    # Electricity Tariff (₹/kWh)
    tariff = [11.50] * num_samples

    df = pd.DataFrame({
        "timestamp": [t.isoformat() for t in timestamps],
        "hour_of_day": hours,
        "day_of_week": day_of_week,
        "cpu_percent": np.round(cpu_percent, 2),
        "memory_percent": np.round(memory_percent, 2),
        "ambient_temp_c": np.round(ambient_temp, 2),
        "it_power_w": np.round(it_power_w, 2),
        "total_facility_power_w": np.round(total_facility_power_w, 2),
        "grid_carbon_g_co2_kwh": np.round(grid_carbon, 1),
        "electricity_tariff_inr": tariff,
        "pue": np.round(pue, 4)
    })

    df.to_csv(output_path, index=False)
    print(f"Generated {num_samples} telemetry samples saved to: {output_path}")
    print(df.head(5))
    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=3000, help="Number of telemetry data points to generate")
    parser.add_argument("--output", type=str, default="ml/data/telemetry_dataset.csv", help="CSV export destination")
    args = parser.parse_args()
    generate_telemetry_dataset(args.samples, args.output)
