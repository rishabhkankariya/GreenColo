#!/usr/bin/env python3
"""
GreenColo: Host Telemetry Agent
Monitors local compute metrics (CPU, RAM, Disk, Network) using psutil
and streams them to the GreenColo FastAPI ingestion service.
"""

import time
import requests
import argparse
import psutil
from datetime import datetime, timezone

def collect_host_metrics(node_id: str, prev_disk, prev_net, interval: float):
    cpu_percent = psutil.cpu_percent(interval=None)
    memory_percent = psutil.virtual_memory().percent

    # Disk I/O
    current_disk = psutil.disk_io_counters()
    disk_read_mbps = 0.0
    disk_write_mbps = 0.0
    if prev_disk and current_disk:
        disk_read_bytes = current_disk.read_bytes - prev_disk.read_bytes
        disk_write_bytes = current_disk.write_bytes - prev_disk.write_bytes
        disk_read_mbps = round((disk_read_bytes / (1024 * 1024)) / interval, 2)
        disk_write_mbps = round((disk_write_bytes / (1024 * 1024)) / interval, 2)

    # Net I/O
    current_net = psutil.net_io_counters()
    net_rx_mbps = 0.0
    net_tx_mbps = 0.0
    if prev_net and current_net:
        rx_bytes = current_net.bytes_recv - prev_net.bytes_recv
        tx_bytes = current_net.bytes_sent - prev_net.bytes_sent
        net_rx_mbps = round((rx_bytes / (1024 * 1024)) / interval, 2)
        net_tx_mbps = round((tx_bytes / (1024 * 1024)) / interval, 2)

    # Temperature (if supported on OS)
    temperature_c = None
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                if entries:
                    temperature_c = entries[0].current
                    break
    except Exception:
        temperature_c = None

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "node_id": node_id,
        "cpu_percent": float(cpu_percent),
        "memory_percent": float(memory_percent),
        "disk_io_read_mbps": max(0.0, disk_read_mbps),
        "disk_io_write_mbps": max(0.0, disk_write_mbps),
        "net_io_rx_mbps": max(0.0, net_rx_mbps),
        "net_io_tx_mbps": max(0.0, net_tx_mbps),
        "temperature_c": temperature_c
    }
    return payload, current_disk, current_net

def main():
    parser = argparse.ArgumentParser(description="GreenColo Host Compute Telemetry Agent")
    parser.add_argument("--node", type=str, default="local_test_node", help="Node identifier")
    parser.add_argument("--interval", type=float, default=2.0, help="Poll interval in seconds")
    parser.add_argument("--endpoint", type=str, default="http://localhost:8000/api/v1/telemetry/host", help="Ingestion URL")
    args = parser.parse_args()

    print("=" * 60)
    print(" GreenColo Host Compute Telemetry Agent")
    print(f" Target Endpoint: {args.endpoint}")
    print(f" Node Identifier: {args.node}")
    print(f" Interval       : {args.interval}s")
    print(" Press Ctrl+C to stop.")
    print("=" * 60)

    prev_disk = psutil.disk_io_counters()
    prev_net = psutil.net_io_counters()

    # Initial prime reading for cpu_percent
    psutil.cpu_percent(interval=None)
    time.sleep(args.interval)

    while True:
        try:
            payload, prev_disk, prev_net = collect_host_metrics(
                node_id=args.node,
                prev_disk=prev_disk,
                prev_net=prev_net,
                interval=args.interval
            )

            try:
                response = requests.post(args.endpoint, json=payload, timeout=3)
                status_mark = "✓" if response.status_code == 200 else f"✗ ({response.status_code})"
            except requests.exceptions.RequestException as e:
                status_mark = f"✗ Connection Error ({type(e).__name__})"

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Node: {payload['node_id']} | "
                  f"CPU: {payload['cpu_percent']:>4.1f}% | RAM: {payload['memory_percent']:>4.1f}% | "
                  f"Disk: {payload['disk_io_read_mbps']} R / {payload['disk_io_write_mbps']} W MB/s | API: {status_mark}")

            time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\nStopped host telemetry agent.")
            break

if __name__ == "__main__":
    main()
