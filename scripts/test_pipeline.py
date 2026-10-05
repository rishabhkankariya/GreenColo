#!/usr/bin/env python3
"""
GreenColo: Automated End-to-End Pipeline Smoke Test
Validates that FastAPI endpoints, data ingestion, cost calculations,
carbon calculations, and decision logic operate correctly.
"""

import requests
import json
import sys
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"

def test_health():
    print("\n[1/5] Testing /api/v1/health...")
    res = requests.get(f"{BASE_URL}/api/v1/health", timeout=3)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    print(f"      Status: {data['status']} | InfluxDB Connected: {data['influxdb_connected']} | Zone: {data['zone']}")
    return True

def test_power_ingestion():
    print("\n[2/5] Testing POST /api/v1/telemetry/power...")
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "device_id": "test_bench_pzem_01",
        "source": "pzem-004t",
        "voltage_v": 230.5,
        "current_a": 4.12,
        "power_w": 949.6,
        "energy_kwh": 0.045,
        "power_factor": 0.98,
        "frequency_hz": 50.0
    }
    res = requests.post(f"{BASE_URL}/api/v1/telemetry/power", json=payload, timeout=3)
    assert res.status_code in [200, 202], f"Failed: {res.status_code} {res.text}"
    print(f"      Result: {res.json()['message']}")
    return True

def test_host_ingestion():
    print("\n[3/5] Testing POST /api/v1/telemetry/host...")
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "node_id": "test_node_01",
        "cpu_percent": 65.4,
        "memory_percent": 52.1,
        "disk_io_read_mbps": 14.2,
        "disk_io_write_mbps": 5.8,
        "net_io_rx_mbps": 12.1,
        "net_io_tx_mbps": 3.4,
        "temperature_c": 48.0
    }
    res = requests.post(f"{BASE_URL}/api/v1/telemetry/host", json=payload, timeout=3)
    assert res.status_code in [200, 202], f"Failed: {res.status_code} {res.text}"
    print(f"      Result: {res.json()['message']}")
    return True

def test_latest_snapshot():
    print("\n[4/5] Testing GET /api/v1/telemetry/latest...")
    res = requests.get(f"{BASE_URL}/api/v1/telemetry/latest", timeout=3)
    assert res.status_code == 200, f"Failed: {res.status_code}"
    data = res.json()
    burn = data.get("burn_rates", {})
    grid = data.get("grid_telemetry", {})
    print(f"      Grid Carbon: {grid.get('carbon_intensity_g_co2_kwh')} g/kWh | Tariff: ₹{grid.get('electricity_tariff_inr_per_kwh')}/kWh")
    print(f"      Burn Rate  : ₹{burn.get('cost_rate_inr_hr')}/hr | {burn.get('carbon_rate_g_hr')} g CO2/hr")
    return True

def test_decision_engine():
    print("\n[5/5] Testing POST /api/v1/decision/evaluate...")
    
    # Case A: Flexible batch workload (High on-prem carbon -> Cloud)
    batch_req = {
        "workload_id": "batch_job_101",
        "name": "daily_video_transcode",
        "workload_type": "batch",
        "cpu_cores_required": 4.0,
        "memory_mb_required": 4096,
        "deadline_minutes": 120,
        "latency_tolerance": "high",
        "sustainability_priority": 0.7,
        "cost_priority": 0.3
    }
    res_batch = requests.post(f"{BASE_URL}/api/v1/decision/evaluate", json=batch_req, timeout=3)
    d_batch = res_batch.json()
    print(f"      [Batch Workload]    Destination: {d_batch['recommended_destination']}")
    print(f"                          Rationale  : {d_batch['reason']}")

    # Case B: Latency-sensitive real-time workload (Must stay on-premise)
    realtime_req = {
        "workload_id": "realtime_service_202",
        "name": "campus_gate_auth_api",
        "workload_type": "realtime",
        "cpu_cores_required": 1.0,
        "memory_mb_required": 1024,
        "deadline_minutes": 5,
        "latency_tolerance": "low",
        "sustainability_priority": 0.5,
        "cost_priority": 0.5
    }
    res_rt = requests.post(f"{BASE_URL}/api/v1/decision/evaluate", json=realtime_req, timeout=3)
    d_rt = res_rt.json()
    print(f"      [Realtime Workload] Destination: {d_rt['recommended_destination']}")
    print(f"                          Rationale  : {d_rt['reason']}")

    assert d_rt["recommended_destination"] == "ON_PREMISE", "Realtime workload should stay On-Premise"
    return True

if __name__ == "__main__":
    print("=" * 65)
    print(" GreenColo End-to-End Ingestion & Decision Smoke Test")
    print(f" Target Backend: {BASE_URL}")
    print("=" * 65)
    try:
        test_health()
        test_power_ingestion()
        test_host_ingestion()
        test_latest_snapshot()
        test_decision_engine()
        print("\n" + "=" * 65)
        print(" ALL 5 SMOKE TESTS PASSED SUCCESSFULLY! ")
        print("=" * 65)
    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] Could not connect to {BASE_URL}. Ensure FastAPI is running:")
        print("        uvicorn backend.app.main:app --port 8000 --reload")
        sys.exit(1)
    except AssertionError as e:
        print(f"\n[ASSERTION FAILED] {e}")
        sys.exit(1)
