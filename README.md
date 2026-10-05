# GreenColo: A Cloud-Driven AI System for Real-Time Energy & Carbon-Aware Optimization in Hybrid Colocation Data Centers

GreenColo is an intelligent cloud-driven optimization system designed to balance energy efficiency, operational electricity costs, and grid carbon emissions across hybrid infrastructure (On-Premises / Lab Nodes vs. Public Cloud / AWS).

---

## 1. System Architecture Overview

The system follows an 8-block data and decision pipeline:

1. **Data Sources:** Live power sensors (ESP32 + PZEM-004T / Smart Plug / IPMI), Electricity Maps API (`IN-WE` zone), and MSEDCL regional electricity tariff.
2. **Data Ingestion:** High-throughput Python FastAPI service validating and normalizing telemetry.
3. **Storage Layer:** InfluxDB v2 for time-series metrics and PostgreSQL for structured workload configurations.
4. **AI/ML Prediction:** XGBoost regressor predicting Power Usage Effectiveness (PUE) and computing power draw.
5. **Decision Engine:** Rules + ML-based multi-objective optimizer evaluating carbon intensity, cost, and SLA constraints.
6. **Orchestration:** Kubernetes scheduler routing containerized jobs to on-premises nodes vs. public cloud.
7. **Observability:** Prometheus metrics collection and real-time Grafana monitoring dashboards.
8. **Supporting Infrastructure:** Terraform Infrastructure as Code, GitHub Actions CI/CD, and Docker containerization.

---

## 2. Quickstart Guide (Local Execution)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start the Backend Service
```bash
# Start FastAPI backend (port 8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation and Swagger UI will be accessible at: `http://localhost:8000/docs`

### Step 3: Run the Mock Power Telemetry Agent
Stream real-time electrical telemetry (Voltage, Current, Power, Energy) directly into the API:
```bash
python agents/mock_power_agent.py --interval 2 --endpoint http://localhost:8000/api/v1/telemetry/power
```

### Step 4: Run the Local Host Compute Telemetry Agent
Stream local CPU, RAM, disk, and network load into the ingestion pipeline:
```bash
python agents/host_agent.py --node local_test_node --interval 2 --endpoint http://localhost:8000/api/v1/telemetry/host
```

### Step 5: Test the Decision Engine
Evaluate placement for an incoming batch job:
```bash
python scheduler/k8s_client.py --name transcode_batch_01 --cpu 2.0 --mem 2048
```

---

## 3. Docker Compose Stack (Full Environment)

To launch InfluxDB, PostgreSQL, Grafana, and the Backend together:
```bash
docker compose up -d
```

- **FastAPI Backend:** `http://localhost:8000`
- **Grafana Dashboard:** `http://localhost:3000` (User: `admin`, Pass: `admin`)
- **InfluxDB UI:** `http://localhost:8086`

---

## 4. Machine Learning Pipeline (PUE Forecasting)

Generate training data and train the XGBoost model:
```bash
# Generate 3,500 time-series telemetry samples
python ml/dataset_generator.py --samples 3500 --output ml/data/telemetry_dataset.csv

# Train and evaluate XGBoost PUE predictor
python ml/train_xgboost.py --data ml/data/telemetry_dataset.csv --out ml/models
```

---

## 5. Physical Hardware Setup (ESP32 + PZEM-004T)

Refer to [`iot/esp32_pzem/README.md`](iot/esp32_pzem/README.md) for pinout diagrams, optocoupler safety precautions, and Arduino flashing instructions.
