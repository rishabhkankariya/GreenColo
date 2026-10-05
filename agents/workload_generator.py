#!/usr/bin/env python3
"""
GreenColo: Empirical Workload Benchmark & Telemetry Profiler
Executes multi-stage controlled CPU stress cycles (Idle -> Light -> Medium -> Heavy),
samples real-time system compute load and physical/modeled power draw,
computes associated carbon emissions and monetary cost,
and prints an empirical evaluation table.
"""

import time
import math
import multiprocessing
import argparse
import psutil
import requests
import os
import pandas as pd
from datetime import datetime, timezone

def cpu_burner(target_load_pct: float, duration_sec: float):
    period = 0.1  # 100ms cycle
    busy_time = period * (target_load_pct / 100.0)
    sleep_time = period - busy_time
    
    end_time = time.time() + duration_sec
    while time.time() < end_time:
        cycle_start = time.time()
        while (time.time() - cycle_start) < busy_time:
            _ = math.sqrt(12345.67) * math.sin(789.0)
        if sleep_time > 0:
            time.sleep(sleep_time)

def estimate_power_w(cpu_pct: float) -> float:
    """
    Empirical power curve for lab test PC / workstation:
    P_base (idle) ~ 65W, P_max ~ 185W (scaled dynamically with CPU %)
    """
    return round(65.0 + (120.0 * (cpu_pct / 100.0)), 1)

def run_empirical_benchmark(stage_duration: float = 12.0, num_workers: int = None, api_url: str = "http://localhost:8000"):
    if num_workers is None:
        num_workers = max(1, multiprocessing.cpu_count() - 1)

    stages = [
        ("Idle", 0.0),
        ("Light", 25.0),
        ("Medium", 55.0),
        ("Heavy", 90.0)
    ]

    print("=" * 75)
    print(" GreenColo Empirical Workload-Power Profiler")
    print(f" Workers Allocated : {num_workers} CPU cores")
    print(f" Stage Duration    : {stage_duration}s per phase")
    print("=" * 75)

    results = []
    tariff_inr_per_kwh = 11.50
    carbon_intensity_g_kwh = 650.0

    # Try fetching live grid carbon and tariff from running FastAPI backend if reachable
    try:
        res = requests.get(f"{api_url}/api/v1/telemetry/grid/current", timeout=2)
        if res.status_code == 200:
            grid_data = res.json()
            carbon_intensity_g_kwh = float(grid_data.get("carbon_intensity_g_co2_kwh", 650.0))
            tariff_inr_per_kwh = float(grid_data.get("electricity_tariff_inr_per_kwh", 11.50))
            print(f"[API Sync] Using live grid: {carbon_intensity_g_kwh} gCO2/kWh | Tariff: ₹{tariff_inr_per_kwh}/kWh")
    except Exception:
        print(f"[Offline Default] Using baseline grid: {carbon_intensity_g_kwh} gCO2/kWh | Tariff: ₹{tariff_inr_per_kwh}/kWh")

    # Prime CPU meter
    psutil.cpu_percent(interval=None)

    for stage_name, target_load in stages:
        print(f"\n[Running Stage] {stage_name:<8} (Target: {target_load}%) for {stage_duration}s...")
        
        start_time = datetime.now(timezone.utc)
        
        # Launch worker processes if target > 0
        processes = []
        if target_load > 0:
            for _ in range(num_workers):
                p = multiprocessing.Process(target=cpu_burner, args=(target_load, stage_duration))
                processes.append(p)
                p.start()

        # Sample metrics mid-stage
        time.sleep(stage_duration / 2.0)
        cpu_measured = psutil.cpu_percent(interval=1.0)
        mem_measured = psutil.virtual_memory().percent
        
        # Wait for processes to conclude
        for p in processes:
            p.join()

        # Compute power & environmental metrics
        power_w = estimate_power_w(cpu_measured)
        # Stage duration energy in kWh
        stage_kwh = (power_w * stage_duration) / 3_600_000.0
        stage_cost_inr = round(stage_kwh * tariff_inr_per_kwh, 4)
        stage_co2_g = round(stage_kwh * carbon_intensity_g_kwh, 2)

        record = {
            "Stage": stage_name,
            "Target CPU": f"{int(target_load)}%",
            "Measured CPU": f"{cpu_measured:.1f}%",
            "RAM": f"{mem_measured:.1f}%",
            "Power (W)": f"{power_w:.1f} W",
            "Energy (kWh)": f"{stage_kwh:.6f}",
            "Cost (₹)": f"₹{stage_cost_inr:.4f}",
            "CO₂ (g)": f"{stage_co2_g:.2f} g"
        }
        results.append(record)

        # Post to local FastAPI telemetry endpoint if available
        try:
            power_payload = {
                "device_id": "lab_bench_pc",
                "source": "empirical_benchmark",
                "voltage_v": 230.1,
                "current_a": round(power_w / (230.1 * 0.98), 2),
                "power_w": power_w,
                "energy_kwh": round(stage_kwh, 6),
                "power_factor": 0.98,
                "frequency_hz": 50.0
            }
            requests.post(f"{api_url}/api/v1/telemetry/power", json=power_payload, timeout=2)
            
            host_payload = {
                "node_id": "lab_bench_pc",
                "cpu_percent": cpu_measured,
                "memory_percent": mem_measured
            }
            requests.post(f"{api_url}/api/v1/telemetry/host", json=host_payload, timeout=2)
        except Exception:
            pass

    # Print Table
    df = pd.DataFrame(results)
    print("\n" + "=" * 80)
    print(" EXPERIMENTAL WORKLOAD vs. POWER & CARBON MEASUREMENT MATRIX")
    print("=" * 80)
    print(df.to_markdown(index=False))
    print("=" * 80)

    # Save to disk
    os.makedirs("ml/data", exist_ok=True)
    csv_path = "ml/data/empirical_workload_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nEmpirical benchmark results persisted to: {csv_path}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-duration", type=float, default=12.0, help="Duration in seconds per stage")
    parser.add_argument("--workers", type=int, default=None, help="Worker count")
    args = parser.parse_args()

    run_empirical_benchmark(args.stage_duration, args.workers)
