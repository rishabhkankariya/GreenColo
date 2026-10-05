#!/usr/bin/env python3
"""
GreenColo: Mock Power Telemetry Agent
Simulates an ESP32 + PZEM-004T energy monitor streaming electrical power readings.
Used for zero-dependency local testing before physical hardware or lab access.
"""

import time
import random
import requests
import argparse
from datetime import datetime, timezone

def generate_power_reading(device_id: str, accumulated_kwh: float, interval_sec: float, state: str = "active"):
    # 230V AC Grid simulation (nominal 230V with +/- 2.5V jitter)
    voltage = round(230.0 + random.uniform(-2.5, 2.5), 1)

    # Current & Power based on operating state
    if state == "idle":
        # PC idle or standby: ~40-60 Watts
        current = round(random.uniform(0.18, 0.28), 2)
        power_factor = 0.92
    elif state == "medium":
        # Moderate computing load: ~180-260 Watts
        current = round(random.uniform(0.80, 1.15), 2)
        power_factor = 0.96
    else:
        # Full batch/transcoding/load: ~450-950 Watts (e.g. heating element / multi-server test)
        current = round(random.uniform(3.50, 4.30), 2)
        power_factor = 0.98

    # Active power P = V * I * PF
    power_w = round(voltage * current * power_factor, 1)

    # Incremental energy delta: kWh = (Watts * seconds) / (1000 * 3600)
    delta_kwh = (power_w * interval_sec) / 3_600_000.0
    accumulated_kwh += delta_kwh

    frequency = round(50.0 + random.uniform(-0.1, 0.1), 1)

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "device_id": device_id,
        "source": "mock_pzem",
        "voltage_v": voltage,
        "current_a": current,
        "power_w": power_w,
        "energy_kwh": round(accumulated_kwh, 4),
        "power_factor": power_factor,
        "frequency_hz": frequency
    }
    return payload, accumulated_kwh

def main():
    parser = argparse.ArgumentParser(description="GreenColo Mock Power Agent")
    parser.add_argument("--device", type=str, default="pzem_bench_01", help="Device identifier")
    parser.add_argument("--interval", type=float, default=2.0, help="Publish interval in seconds")
    parser.add_argument("--endpoint", type=str, default="http://localhost:8000/api/v1/telemetry/power", help="Ingestion URL")
    args = parser.parse_args()

    print("=" * 60)
    print(" GreenColo Mock Power Telemetry Agent")
    print(f" Target Endpoint: {args.endpoint}")
    print(f" Device ID      : {args.device}")
    print(f" Interval       : {args.interval} seconds")
    print(" Press Ctrl+C to stop.")
    print("=" * 60)

    accumulated_kwh = 0.0150
    step = 0

    while True:
        try:
            # Vary states over time to create realistic workload cycles:
            # 0-20 steps idle, 21-50 steps medium, 51-80 steps full load
            cycle = step % 90
            if cycle < 25:
                state = "idle"
            elif cycle < 55:
                state = "medium"
            else:
                state = "active"

            payload, accumulated_kwh = generate_power_reading(
                device_id=args.device,
                accumulated_kwh=accumulated_kwh,
                interval_sec=args.interval,
                state=state
            )

            try:
                response = requests.post(args.endpoint, json=payload, timeout=3)
                status_mark = "✓" if response.status_code == 200 else f"✗ ({response.status_code})"
            except requests.exceptions.RequestException as e:
                status_mark = f"✗ Connection Error ({type(e).__name__})"

            print(f"[{datetime.now().strftime('%H:%M:%S')}] [{state.upper():<6}] "
                  f"V: {payload['voltage_v']}V | I: {payload['current_a']}A | "
                  f"P: {payload['power_w']}W | E: {payload['energy_kwh']} kWh | API: {status_mark}")

            step += 1
            time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\nStopped mock power agent.")
            break

if __name__ == "__main__":
    main()
