# IMPLEMENTATION MASTER PLAN: GreenColo (CloudGen / TYCC106)
**Project Title:** A Cloud-Driven AI System for Real-Time Energy & Carbon-Aware Optimization in Hybrid Colocation Data Centers  
**Team Name:** CloudGen (Group ID: TYCC106)  
**Institution:** MIT Art, Design & Technology University, Pune — School of Computing  
**Academic Year:** 2026–27 | **Event:** IdeaSpark & PBL Review  
**Guide Code:** M126 (Prof. Dr. Abhishek M. Dhone)  
**Status:** Implementation Phase (Zero-Blocker Local-First Setup)

---

## 1. Official Architecture Mapping (8-Block System)

Directly mapped to the verified system architecture diagram:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. DATA SOURCES                                                                             │
│   • Hardware Sensor (Smart Plug / IPMI / PZEM-004T) -> Live Power (Watts)                   │
│   • Electricity Maps API (Zone: IN-WE)              -> Live Grid Carbon Intensity (gCO2/kWh)│
│   • MSEDCL Tariff API / Billing Model               -> Electricity Tariff Rate (₹/kWh)      │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │ Polled / Pushed (Every 30–60s)
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. DATA INGESTION: FastAPI Ingestion Service (Python)                                       │
│   • Collects & Normalizes Data from All Sources                                             │
│   • Validates Schemas (Pydantic) & Timestamps Readings                                      │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. STORAGE LAYER: InfluxDB Time-Series Database                                             │
│   • Stores Live Time-Series Readings (Power, Carbon, Cost, Energy)                          │
│   • PostgreSQL: Structured metadata, workload specifications, configuration                 │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 4. AI/ML PREDICTION: XGBoost / ML Model Prediction Engine                                   │
│   • Predicts: PUE (Power Usage Effectiveness), Workload Demand & Power Draw                 │
│   • Uses: Historical + Live Telemetry                                                       │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │ Predictions
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 5. DECISION ENGINE: Rules + ML-Based Optimizer                                              │
│   • Compares Options: Predicted Carbon Intensity, Cost, Predicted PUE, SLA Constraints      │
│   • Decides Best Place for Each Workload: ON-PREMISE vs. PUBLIC CLOUD                       │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │ Placement Decision
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 6. ORCHESTRATION: Kubernetes Scheduler                                                      │
│   • Enforces Decision Engine's Choice (Containerized Workload Placement / Redeployment)     │
│   • Target A: On-Prem Node (College Server / Lab PC)                                        │
│   • Target B: Public Cloud (AWS / Azure / GCP)                                              │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │ Telemetry & State
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 7. OBSERVABILITY: Prometheus & Grafana Dashboard                                            │
│   • Prometheus: Collects Live Metrics from All Components                                   │
│   • Grafana: Live Visualization of Energy Used (kWh), CO₂ Emitted / Avoided, Cost Saved (₹),│
│     Workload Placement Distribution, and System Health                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
  ▲                                            ▲                                            ▲
  │                                            │                                            │
┌─┴────────────────────────────────────────────┴────────────────────────────────────────────┴─┐
│ 8. SUPPORTING INFRASTRUCTURE (Provisioning & Deployment)                                    │
│   • Terraform: Infrastructure as Code (Provisions Cloud Resources on AWS / Azure / GCP)     │
│   • GitHub Actions: CI/CD Pipeline (Builds, Tests & Deploys Services & Schedulers)          │
│   • Docker: Containerization (All Services Packaged as Containers via Docker Compose)        │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Decoupling Strategy: Zero-Blocker Implementation

To eliminate external dependencies (such as pending college rack permissions, administrative approvals, or IT physical access), the software pipeline uses a **Strict Adapter Pattern**.

### Why This Works
1. **Schema Independence:** Downstream components (FastAPI, InfluxDB, XGBoost, Decision Engine, Grafana) only consume standardized JSON schemas.
2. **Phase 1 Testbed:** Electrical power is measured using a bench setup (ESP32 + PZEM-004T on a controlled load) or an automated Mock Generator.
3. **Phase 2 Expansion:** When college server/IPMI access is granted, only a 40-line `ipmi_adapter.py` is written to query BMC/PDU metrics and send them to the existing `/api/v1/telemetry/power` endpoint. No backend, ML, or dashboard code is altered.

```
+---------------------------------------+
|           Producers (Interchangeable) |
|   • ESP32 + PZEM-004T (Bench Load)    |
|   • Synthetic Mock Telemetry Daemon   | -----> [ /api/v1/telemetry/power ]
|   • Future College Server IPMI Script |
+---------------------------------------+
                                                         |
                                                         v
                                        +----------------------------------+
                                        | Downstream Pipeline (Unchanged)  |
                                        |  • InfluxDB                      |
                                        |  • Real-Time Cost/CO2 Engine     |
                                        |  • XGBoost Prediction Model      |
                                        |  • Multi-Objective Decision      |
                                        |  • Grafana Live Dashboards       |
                                        +----------------------------------+
```

---

## 3. Standardized Data Schemas & API Contracts

### 3.1 Hardware Power Telemetry (`/api/v1/telemetry/power`)
```json
{
  "timestamp": "2026-09-25T21:30:00.000Z",
  "device_id": "pzem_node_01",
  "source": "pzem-004t",
  "voltage_v": 230.4,
  "current_a": 4.12,
  "power_w": 949.2,
  "energy_kwh": 0.048,
  "power_factor": 0.98,
  "frequency_hz": 50.0
}
```

### 3.2 Host Compute Telemetry (`/api/v1/telemetry/host`)
```json
{
  "timestamp": "2026-09-25T21:30:00.000Z",
  "node_id": "test_server_local",
  "cpu_percent": 64.5,
  "memory_percent": 52.8,
  "disk_io_read_mbps": 12.4,
  "disk_io_write_mbps": 4.1,
  "net_io_rx_mbps": 8.5,
  "net_io_tx_mbps": 2.1,
  "temperature_c": 46.5
}
```

### 3.3 Carbon & Grid Telemetry (`/api/v1/telemetry/grid`)
```json
{
  "timestamp": "2026-09-25T21:30:00.000Z",
  "zone": "IN-WE",
  "carbon_intensity_g_co2_kwh": 654.0,
  "fossil_fuel_percentage": 78.5,
  "renewable_percentage": 21.5,
  "electricity_tariff_inr_per_kwh": 11.50
}
```

### 3.4 Workload Placement Decision Request (`/api/v1/decision/evaluate`)
```json
{
  "workload_id": "batch_job_4091",
  "name": "image_transcoder_job",
  "workload_type": "batch",
  "cpu_cores_required": 2,
  "memory_mb_required": 2048,
  "deadline_minutes": 120,
  "latency_tolerance": "high",
  "sustainability_priority": 0.7,
  "cost_priority": 0.3
}
```

---

## 4. Repository Structure & Component Manifest

```
PBL Project/
├── IMPLEMENTATION.md               # Master technical plan & specifications (This file)
├── docker-compose.yml              # Multi-container orchestration (InfluxDB, Grafana, API, DB)
├── .env.example                    # Template environment variables
├── requirements.txt                # Python backend & ML dependencies
├── backend/
│   ├── Dockerfile
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application root & middleware
│   │   ├── config.py               # Pydantic BaseSettings (.env loading)
│   │   ├── models/
│   │   │   ├── schemas.py          # Request & response Pydantic models
│   │   │   └── database.py         # SQLAlchemy & InfluxDB schema bindings
│   │   ├── routers/
│   │   │   ├── telemetry.py        # /api/v1/telemetry (Power, Host, Grid)
│   │   │   ├── decision.py         # /api/v1/decision (Placement routing)
│   │   │   └── analytics.py        # /api/v1/analytics (Historical aggregates)
│   │   └── services/
│   │       ├── influx_service.py   # InfluxDB v2 Client (writes & flux queries)
│   │       ├── carbon_service.py   # Electricity Maps API polling & caching
│   │       ├── cost_engine.py      # MSEDCL tariff calculation engine
│   │       └── decision_engine.py  # Multi-objective placement algorithm
├── agents/
│   ├── host_agent.py               # psutil daemon collecting local system load
│   ├── mock_power_agent.py         # Realistic PZEM simulator for test & CI
│   └── ipmi_agent.py               # Future: IPMI/BMC server collector
├── iot/
│   └── esp32_pzem/
│       ├── esp32_pzem.ino          # Arduino C++ firmware for ESP32 + PZEM-004T
│       ├── config.h.example        # WiFi SSID, Pass, and Backend API URL
│       └── README.md               # Wiring schematics and safety checklist
├── ml/
│   ├── dataset_generator.py        # Synthetic & captured time-series generator
│   ├── feature_engineering.py      # Feature extraction (lag, rolling means, time)
│   ├── train_xgboost.py            # Model training & cross-validation script
│   └── models/                     # Exported model artifacts (.json / .pkl)
├── scheduler/
│   ├── k8s_client.py               # Kubernetes Python client for pod dispatch
│   └── sample_workloads/
│       ├── batch_job.yaml          # Sample containerized CPU stress job
│       └── web_service.yaml        # Sample continuous service
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   │   └── datasources.yaml    # Automatic InfluxDB Flux connection
    │   └── dashboards/
    │       └── dashboards.yaml     # Dashboard provider configuration
    └── dashboards/
        └── greencolo_master.json   # Live dashboard (Power, CO2, Cost, Routing)
```

---

## 5. Phased Implementation Roadmap & Checklists

### Milestone 1: Local Stack & Telemetry Ingestion (Days 1–3)
- [ ] Create `docker-compose.yml` with:
  - `influxdb:2.7` (mapped to port 8086)
  - `postgres:15` (mapped to port 5432)
  - `grafana:10.2` (mapped to port 3000)
  - `backend` (FastAPI mapped to port 8000)
- [ ] Implement FastAPI server with `/api/v1/telemetry/power` and `/api/v1/telemetry/host`.
- [ ] Implement `influx_service.py` to write incoming points with tags (`device_id`, `node_id`) and fields (`power_w`, `voltage_v`, `current_a`).
- [ ] Build `agents/mock_power_agent.py` to simulate realistic PZEM readings and verify real-time writes.
- [ ] Write `iot/esp32_pzem/esp32_pzem.ino` firmware with HardwareSerial communication to PZEM-004T and HTTP POST client.

### Milestone 2: Host Metrics & Workload-Power Correlation (Days 4–6)
- [ ] Implement `agents/host_agent.py` using `psutil`:
  - Poll CPU, memory, disk I/O, network I/O every 2 seconds.
  - Send metrics to `/api/v1/telemetry/host`.
- [ ] Build a workload stress utility (`stress-ng` or Python multi-processing script) to generate controlled load cycles (Idle -> 30% -> 60% -> 90% CPU).
- [ ] Correlate electrical power draw (Watts) with CPU utilization curve in InfluxDB.

### Milestone 3: Carbon Intensity & Electricity Tariff Engine (Days 7–9)
- [ ] Implement `backend/app/services/carbon_service.py`:
  - Integrate Electricity Maps API with zone `IN-WE` (Western India / Maharashtra).
  - Add fallback caching (last known valid intensity + mock fallback when offline).
- [ ] Implement `backend/app/services/cost_engine.py`:
  - Support MSEDCL commercial tariff bands (or flat rate ₹11.50/kWh baseline).
  - Calculate instantaneous cost rate (₹/hr) and accumulated session cost.
- [ ] Persist real-time calculated fields in InfluxDB:
  - `cost_rate_inr_hr = (power_w / 1000) * tariff_rate`
  - `carbon_rate_g_hr = (power_w / 1000) * carbon_intensity_g_co2_kwh`

### Milestone 4: Live Observability & Pre-provisioned Grafana Dashboards (Days 10–12)
- [ ] Create automated Grafana datasource provisioning for InfluxDB (using Flux query language).
- [ ] Design and export `grafana/dashboards/greencolo_master.json`:
  - Stat panel: Current Power Draw (Watts)
  - Stat panel: Grid Carbon Intensity (gCO2/kWh)
  - Stat panel: Total Energy (kWh) and Total Cost (₹)
  - Stat panel: CO2 Avoided (kg CO2e)
  - Time-series graph: Power Draw vs. CPU Utilization
  - Time-series graph: Carbon Intensity & Placement Decisions over time

### Milestone 5: Machine Learning (PUE & Demand Forecasting) (Days 13–16)
- [ ] Generate or record training dataset:
  - Features: `cpu_percent`, `memory_percent`, `io_rate`, `ambient_temp`, `hour_of_day`, `day_of_week`.
  - Target: `power_w` and `pue`.
- [ ] Train XGBoost Regressor model using Scikit-Learn / XGBoost Python library.
- [ ] Evaluate with MAE, RMSE, and R² score; serialize model to `ml/models/xgboost_pue_model.json`.
- [ ] Wrap model inference in FastAPI for real-time predictions.

### Milestone 6: Multi-Objective Decision Engine (Days 17–19)
- [ ] Implement placement decision logic in `backend/app/services/decision_engine.py`:
  - Objective: Minimize weighted cost and carbon impact while satisfying deadline and latency constraints.
  - Multi-Objective Score:
    $$\text{Score} = w_{\text{carbon}} \cdot \hat{C} + w_{\text{cost}} \cdot \hat{P} + w_{\text{energy}} \cdot \hat{E}$$
  - Hard guardrails: If SLA risk > threshold, do not migrate.
- [ ] Expose endpoint `/api/v1/decision/evaluate` returning target destination: `ON_PREM_LOCAL` or `AWS_CLOUD`.

### Milestone 7: Containerization & Kubernetes Dispatcher (Days 20–22)
- [ ] Containerize test batch workloads using Docker.
- [ ] Implement `scheduler/k8s_client.py`:
  - Read decision output.
  - Submit Kubernetes Job manifest with `nodeAffinity` or deploy to designated cluster context.
  - Target placement: Local node (Lab/College PC) vs. Public Cloud (AWS).
- [ ] Demonstrate end-to-end flow: High carbon / cost on-premises triggers cloud dispatch; low carbon on-premises triggers local execution.

### Milestone 8: College Server / Rack Integration (Post-Approval)
- [ ] Configure `agents/ipmi_agent.py` to poll college server BMC via `ipmitool sensor` or Redfish API.
- [ ] Point IPMI agent to the existing `/api/v1/telemetry/power` endpoint.
- [ ] Validate that the entire system operates transparently with live college data.

---

## 6. Safety & Hardware Guidelines

1. **Mains Electricity Safety (PZEM-004T):**  
   The PZEM-004T connects to 230V AC mains. All mains connections must be enclosed in an insulated junction box. Do not touch bare copper or screw terminals under load. Always utilize the non-invasive split-core Current Transformer (CT) clamp.
2. **Optocoupler Isolation:**  
   The PZEM-004T board features optical isolation between the high-voltage measurement circuit and the 5V/3.3V UART pins connected to the ESP32. Ensure the isolation barrier is not bridged.
3. **Lab Safety:**  
   For preliminary testing, use a standard lab desktop PC, laptop charger, or small controlled appliance before connecting to rack power distribution units (PDUs).

---

## 7. Verification & Testing Commands

### Backend & Containers
```bash
# Start the full telemetry and monitoring stack
docker compose up -d

# Verify containers are healthy
docker compose ps

# View FastAPI backend logs
docker compose logs -f backend
```

### Telemetry Pipeline Testing
```bash
# Send test power measurement
curl -X POST "http://localhost:8000/api/v1/telemetry/power" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test_plug_01",
    "source": "manual_test",
    "voltage_v": 230.1,
    "current_a": 2.1,
    "power_w": 483.21,
    "energy_kwh": 0.012,
    "power_factor": 0.97,
    "frequency_hz": 50.0
  }'

# Run mock power generator daemon (1 reading every 2 seconds)
python agents/mock_power_agent.py --interval 2 --endpoint http://localhost:8000/api/v1/telemetry/power
```

### InfluxDB Verification
```bash
# Query recent points inside InfluxDB
docker exec -it greencolo_influxdb influx query \
  'from(bucket: "greencolo_telemetry") |> range(start: -5m) |> filter(fn: (r) => r._measurement == "power_consumption")'
```

---

*Document finalized and active for implementation tracking.*
