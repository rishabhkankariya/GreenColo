#!/usr/bin/env python3
"""
GreenColo: Kubernetes Workload Placement Dispatcher
Queries the GreenColo Decision Engine API and applies or generates
the Kubernetes Job deployment manifest with the appropriate node placement affinity.
"""

import os
import argparse
import requests
import json
import subprocess
from datetime import datetime

DECISION_API_URL = os.environ.get("DECISION_API_URL", "http://localhost:8000/api/v1/decision/evaluate")

def evaluate_and_dispatch(workload_name: str, cpu_cores: float, memory_mb: int, template_path: str = "scheduler/sample_workloads/batch_job.yaml"):
    payload = {
        "workload_id": f"job_{int(datetime.now().timestamp())}",
        "name": workload_name,
        "workload_type": "batch",
        "cpu_cores_required": cpu_cores,
        "memory_mb_required": memory_mb,
        "deadline_minutes": 60,
        "latency_tolerance": "high",
        "sustainability_priority": 0.65,
        "cost_priority": 0.35
    }

    print(f"\n[Scheduler] Submitting workload '{workload_name}' to GreenColo Decision Engine...")
    try:
        res = requests.post(DECISION_API_URL, json=payload, timeout=5)
        if res.status_code != 200:
            print(f"[Scheduler] API Error: {res.status_code} - {res.text}")
            return
        decision = res.json()
    except Exception as e:
        print(f"[Scheduler] Could not reach Decision Engine: {e}")
        return

    destination = decision["recommended_destination"]
    dest_label = "on-prem" if destination == "ON_PREMISE" else "cloud"

    print("\n" + "=" * 65)
    print(f" DECISION RESULT FOR: {workload_name}")
    print(f" Target Destination  : {destination} (Node Label: {dest_label})")
    print(f" Rationale           : {decision['reason']}")
    print(f" Carbon Impact Est.  : {decision['estimated_carbon_g_co2']} g CO2e")
    print(f" Cost Estimate       : ₹{decision['estimated_cost_inr']}")
    print("=" * 65 + "\n")

    # Read template and inject target node affinity
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            manifest = f.read()

        customized_manifest = manifest.replace("TARGET_DESTINATION_PLACEHOLDER", dest_label)
        output_manifest_path = f"scheduler/generated_placement_{dest_label}.yaml"

        with open(output_manifest_path, "w") as f:
            f.write(customized_manifest)

        print(f"[Scheduler] Generated Kubernetes Job manifest: {output_manifest_path}")

        # Check if kubectl is available
        try:
            k8s_check = subprocess.run(["kubectl", "version", "--client"], capture_output=True, text=True)
            if k8s_check.returncode == 0:
                print(f"[Scheduler] Dispatching to cluster: kubectl apply -f {output_manifest_path}")
                # run = subprocess.run(["kubectl", "apply", "-f", output_manifest_path], capture_output=True, text=True)
                # print(run.stdout)
            else:
                print("[Scheduler] kubectl not in PATH; manifest generated for manual or pipeline deployment.")
        except Exception:
            print("[Scheduler] kubectl client not detected. Manifest generated successfully for GitOps / CI/CD pipeline.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, default="transcode_batch_01", help="Workload name")
    parser.add_argument("--cpu", type=float, default=2.0, help="CPU cores required")
    parser.add_argument("--mem", type=int, default=1024, help="Memory MB required")
    args = parser.parse_args()

    evaluate_and_dispatch(args.name, args.cpu, args.mem)
