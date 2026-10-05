# GreenColo — Final Project Summary

> **Project:** A Cloud-Driven AI System for Real-Time Energy & Carbon-Aware Optimization in Hybrid Colocation Data Centers

## 1. Project Vision

GreenColo makes **workload placement more energy-, carbon-, and cost-aware** across:

- On-premise/college infrastructure
- Public cloud infrastructure

It observes:

- Server/workload utilization
- Electrical power and energy
- Grid carbon intensity
- Electricity cost

It then uses **prediction + decision logic** to determine where an eligible workload should run.

**Key distinction:** Kubernetes executes the placement decision; it is not the sustainability decision-maker.

### One-line explanation

> **GreenColo measures energy and workload conditions, predicts future demand, evaluates carbon and cost, decides whether an eligible workload should run on-premise or in the cloud, and uses Kubernetes to execute that decision.**

---

## 2. Problem

A data center continuously runs workloads, but operating conditions change over time:

- Electricity can have different carbon intensity.
- Electricity costs can vary.
- Server utilization changes.
- Workload demand changes.
- Cloud and on-premise resources can differ in availability and cost.

Traditional scheduling mainly considers:

```text
CPU
RAM
Availability
Latency
```

GreenColo investigates:

> **Can workload placement also consider energy consumption, carbon intensity, and electricity cost?**

This is **not** about physically switching a data center from coal to solar/wind. It is about making workload placement more energy/carbon/cost aware.

---

## 3. Important Clarification

GreenColo does **not** mean:

```text
Coal
 ↓
OFF
 ↓
Solar
```

Instead, it asks:

```text
Where should this workload run?
```

### Example A — Flexible workload

```text
Low urgency
Can tolerate some delay
```

If on-premise conditions are less favorable and cloud satisfies the requirements:

```text
Workload A
     ↓
Cloud
```

### Example B — Critical workload

```text
High priority
Strict latency
Requires local resources
```

It can remain:

```text
Workload B
     ↓
On-Premise
```

> **The workload may move between execution environments; the physical electricity source of the data center does not.**

---

## 4. Overall Architecture

```text
                 DATA SOURCES
                     │
       ┌─────────────┼──────────────┐
       │             │              │
       ▼             ▼              ▼
   Server/PC      PZEM/IPMI    Electricity Maps
   telemetry       Power data      Carbon data
       │             │              │
       └─────────────┼──────────────┘
                     │
                     ▼
                  FastAPI
                     │
                     ▼
                 InfluxDB
                     │
        ┌────────────┼─────────────┐
        │            │             │
        ▼            ▼             ▼
     History      Carbon         Cost
        │            │             │
        └────────────┼─────────────┘
                     ▼
                  XGBoost
                     │
                     ▼
              Decision Engine
                     │
               ┌─────┴─────┐
               ▼           ▼
           ON-PREM        CLOUD
               │           │
               ▼           ▼
          Kubernetes    Kubernetes
               │           │
               └─────┬─────┘
                     ▼
                  Workload
                     │
                     ▼
               Monitoring
                     │
                     └──────→ Feedback
```

---

## 5. Main Components

### 5.1 Server/PC Telemetry

Potential metrics:

```text
CPU utilization
RAM utilization
Disk I/O
Network I/O
Workload information
Timestamp
```

Initially these can come from your own PC. Later they can come from the college server/monitoring system.

### 5.2 PZEM-004T

PZEM provides:

```text
Voltage
Current
Power
Energy
Power Factor
Frequency
```

Flow:

```text
Electrical Load
      ↓
PZEM-004T
      ↓
ESP32
      ↓
Wi-Fi
      ↓
FastAPI
```

### 5.3 Electricity Maps

Target metric:

```text
gCO₂eq/kWh
```

Initially this can be mocked.

Later:

```text
Electricity Maps API
       ↓
Carbon intensity
       ↓
FastAPI
       ↓
InfluxDB
```

### 5.4 Electricity Tariff

Prototype:

```text
Configurable/mock tariff
```

Later:

```text
College electricity bill
+
Applicable MSEDCL tariff information
```

The actual college bill is preferable because the applicable tariff depends on the relevant category and billing structure.

---

## 6. Development Strategy

College server access and hardware integration are not available yet.

Therefore:

```text
PROTOTYPE
   ↓
COLLEGE INTEGRATION
```

Do not make college access a dependency for building the entire system.

---

## 7. Prototype Setup

### Physical test setup

```text
Boiler plate / controlled electrical load
       ↓
PZEM-004T
       ↓
ESP32
```

### Software test setup

```text
Own PC
 ↓
Mock/server telemetry
```

### External data

```text
Mock carbon intensity
Mock/configurable tariff
```

This allows the complete pipeline to be built before college access is available.

---

## 8. Why Start With a Boiler Plate?

The boiler plate is **not the final data-center workload**.

It is the first controlled electrical load.

The first objective is:

> **Can we measure real electrical consumption and send it into our software system?**

First milestone:

```text
Boiler Plate
     ↓
PZEM
     ↓
ESP32
     ↓
FastAPI
     ↓
InfluxDB
     ↓
Grafana
```

Later, this expands to a computer/server workload.

---

# 9. Development Roadmap

## Phase 1 — Electrical Measurement

Build:

```text
Boiler Plate
 ↓
PZEM-004T
 ↓
ESP32
```

Output:

```text
Voltage
Current
Power
Energy
Power Factor
Frequency
```

**Deliverable:** Real electrical measurements from ESP32.

---

## Phase 2 — IoT Data Transmission

```text
PZEM
 ↓
ESP32
 ↓
Wi-Fi
 ↓
FastAPI
```

Example payload:

```json
{
  "device_id": "pzem-001",
  "voltage": 230.2,
  "current": 4.15,
  "power": 945.3,
  "energy": 0.016,
  "power_factor": 0.98,
  "frequency": 50
}
```

---

## Phase 3 — Backend

Use:

```text
Python
FastAPI
```

Responsibilities:

- Receive telemetry
- Validate data
- Normalize data
- Timestamp readings
- Store readings
- Provide APIs to dashboards/services

Possible endpoints:

```text
POST /api/telemetry/power
GET  /api/telemetry/latest
GET  /api/telemetry/history
GET  /api/health
```

---

## Phase 4 — Storage

### InfluxDB

Use for time-series information:

```text
Power
Energy
Voltage
Current
CPU
RAM
Network
Carbon intensity
```

Example:

```text
timestamp       power   voltage   current
10:00           945W    230.2V    4.15A
10:01           948W    230.1V    4.16A
10:02           941W    230.3V    4.13A
```

### PostgreSQL

Use for structured/configuration data:

```text
Servers
Workloads
Workload types
Configuration
Decision records
Cloud information
```

---

## Phase 5 — Grafana

```text
InfluxDB
   ↓
Grafana
```

Initial dashboard:

```text
Power
Voltage
Current
Energy
Power Factor
Frequency
```

Later:

```text
CPU
RAM
Workload
Carbon intensity
CO₂ emissions
Cost
Decision
```

---

## Phase 6 — Server/Workload Monitoring

Use your own PC initially.

Collect:

```text
CPU
RAM
Disk
Network
```

Use a test workload such as a CPU-intensive Python program.

Investigate:

```text
Workload
   ↓
CPU utilization
   ↓
Power consumption
```

This provides the foundation for the ML dataset.

---

## Phase 7 — Cost Calculation

Basic calculation:

```text
Energy × Tariff = Cost
```

Example:

```text
Energy = 0.95 kWh
Tariff = ₹10/kWh

Cost = ₹9.50
```

Prototype: configurable tariff.

Later: actual applicable college tariff/bill information.

---

## Phase 8 — Carbon Calculation

Basic calculation:

```text
Energy × Carbon Intensity = Estimated CO₂
```

Example:

```text
Energy = 0.95 kWh
Carbon intensity = 650 gCO₂eq/kWh

Estimated carbon = 617.5 gCO₂eq
```

Prototype: mock carbon values.

Later: Electricity Maps.

---

## Phase 9 — Dataset

Potential fields:

```text
Timestamp
CPU
RAM
Disk
Network
Power
Energy
Carbon intensity
Tariff
Cost
Workload
Workload type
Criticality
```

Example:

| Time | CPU | RAM | Power | Carbon | Cost | Workload |
|---|---:|---:|---:|---:|---:|---|
| 10:00 | 20% | 42% | 310W | 600 | ₹3.1 | Idle |
| 10:01 | 35% | 44% | 350W | 610 | ₹3.5 | Batch |
| 10:02 | 65% | 48% | 450W | 620 | ₹4.5 | Batch |
| 10:03 | 80% | 51% | 520W | 630 | ₹5.2 | Batch |

---

## 10. Time-Series Data and Training

Suitable development formats:

```text
CSV
Parquet
```

**Parquet is not mandatory for XGBoost training.**

You can start with:

```text
InfluxDB → Pandas DataFrame → Training
```

and later export to Parquet if useful.

---

## 11. Phase 10 — Machine Learning

Primary model:

> **XGBoost**

Possible prediction targets:

```text
Future power consumption
```

or:

```text
Future workload demand
```

Possible input features:

```text
CPU
RAM
Previous power
Previous workload
Time of day
Day of week
Historical energy
```

Flow:

```text
Historical Data
      ↓
Feature Engineering
      ↓
XGBoost
      ↓
Prediction
```

> **XGBoost predicts. It does not make the final workload-placement decision.**

---

## 12. Phase 11 — Decision Engine

The Decision Engine combines:

```text
Current conditions
+
ML prediction
+
Carbon
+
Cost
+
Available resources
+
Workload criticality
+
Latency/SLA requirements
```

Then evaluates:

```text
ON-PREMISE
vs
CLOUD
```

### Example

Flexible batch workload:

```text
On-Prem:
Higher estimated carbon
Higher estimated cost

Cloud:
Lower estimated carbon
Acceptable cost
Available resources

→ Cloud can be recommended
```

Critical workload:

```text
Critical application
Strict latency

→ Keep On-Premise
```

The system should not blindly move everything.

---

## 13. Recommendation Mode First

Initially, the system should **recommend** rather than automatically move workloads.

Example:

```text
Current Location:
ON-PREMISE

Recommended Location:
CLOUD

Reason:
Lower estimated carbon
Acceptable cost
Resources available
Workload is flexible
```

This makes validation easier.

---

## 14. Phase 12 — Docker

Containerize:

```text
FastAPI
InfluxDB
Grafana
ML service
Decision service
```

Initial local environment:

```text
Docker Compose
```

---

## 15. Phase 13 — Kubernetes

Kubernetes is the **execution/orchestration layer**.

Remember:

```text
XGBoost
= Predictor

Decision Engine
= Decision maker

Kubernetes
= Executor
```

Architecture:

```text
Decision Engine
      │
      ├──────────────┐
      ▼              ▼
On-Prem K8s       Cloud K8s
      │              │
      ▼              ▼
 Workload          Workload
```

Kubernetes handles:

- Container scheduling
- Resource allocation
- Starting/stopping containers
- Health checks
- Restarting failed workloads
- Networking
- Placement onto nodes

---

## 16. Workload Migration / Placement

For the MVP, do not claim:

> "We perform live VM migration."

Use:

> **Workload placement/redeployment**

Example:

```text
Current:
On-Prem Kubernetes

Decision:
Cloud is more suitable

↓

Safely terminate/redeploy eligible workload

↓

Cloud Kubernetes
```

Use a suitable stateless or repeatable batch workload for demonstration.

---

# 17. Final GreenColo Flow

```text
                         ┌──────────────────────┐
                         │     DATA SOURCES     │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
       Server Metrics         PZEM + ESP32        Electricity Maps
       CPU/RAM/etc.           Power/Energy        Carbon intensity
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    ▼
                               ┌─────────┐
                               │ FastAPI │
                               └────┬────┘
                                    ▼
                         ┌───────────────────┐
                         │     InfluxDB      │
                         │  Time-series data │
                         └─────────┬─────────┘
                                   │
                       ┌───────────┼───────────┐
                       ▼           ▼           ▼
                     Energy      Cost        Carbon
                       │           │           │
                       └───────────┼───────────┘
                                   ▼
                              ┌─────────┐
                              │ XGBoost │
                              └────┬────┘
                                   │
                              Prediction
                                   │
                                   ▼
                         ┌─────────────────┐
                         │ Decision Engine │
                         └────────┬────────┘
                                  │
                       ┌──────────┴──────────┐
                       ▼                     ▼
                  ON-PREMISE              CLOUD
                       │                     │
                       ▼                     ▼
                  Kubernetes            Kubernetes
                       │                     │
                       └──────────┬──────────┘
                                  ▼
                              Workload
                                  │
                                  ▼
                            Monitor Again
                                  │
                                  └──────→ Feedback
```

---

# 18. Technology Stack

| Layer | Technologies |
|---|---|
| Hardware | ESP32, PZEM-004T, controlled electrical load |
| Embedded | C/C++, Arduino IDE, Wi-Fi, HTTP/REST |
| Backend | Python, FastAPI |
| Time-series DB | InfluxDB |
| Structured DB | PostgreSQL |
| Visualization | Grafana |
| Monitoring | Prometheus |
| ML | Python, Pandas, NumPy, Scikit-learn, XGBoost, Jupyter |
| External data | Electricity Maps API, MSEDCL tariff/billing information, college server telemetry |
| Containerization | Docker, Docker Compose |
| Orchestration | Kubernetes |
| Cloud | AWS |
| Infrastructure | Terraform |
| CI/CD | GitHub Actions |
| Version control | Git/GitHub |
| Development/testing | VS Code, Postman |

---

# 19. College Integration Plan

Current status:

```text
College access = NOT AVAILABLE
```

### Build now

```text
PZEM + ESP32
Mock server metrics
Mock carbon
Configurable tariff
FastAPI
InfluxDB
PostgreSQL
Grafana
ML
Decision Engine
Docker
Kubernetes test environment
Cloud test environment
```

### Integrate later

```text
College server metrics
Actual rack/server power
IPMI/BMC if available
Actual workload information
College electricity bill
Actual tariff
Approved network access
Approved PZEM installation
```

---

# 20. Source-Independent Architecture

The ingestion layer should be source-independent.

### Today

```text
Mock Generator
     ↓
FastAPI
```

### Later

```text
College Monitoring System
     ↓
Adapter
     ↓
FastAPI
```

Similarly:

### Today

```text
PZEM → ESP32 → FastAPI
```

### Later

```text
IPMI/PZEM/other approved source
              ↓
           Adapter
              ↓
           FastAPI
```

Everything after FastAPI remains the same.

> **College integration becomes a data-source replacement rather than a complete project rewrite.**

---

# 21. Five Major Development Milestones

## Milestone 1 — Energy Monitor

```text
Boiler Plate
 ↓
PZEM
 ↓
ESP32
 ↓
FastAPI
 ↓
InfluxDB
 ↓
Grafana
```

**Goal:** Real-time electrical measurement.

## Milestone 2 — Digital Test Server

```text
PC/server
 ↓
CPU/RAM/Disk/Network
 +
PZEM
 ↓
FastAPI
 ↓
InfluxDB
```

**Goal:** Correlate workload activity with actual power.

## Milestone 3 — Carbon & Cost

```text
Energy
 ├──→ Cost
 └──→ Carbon
```

**Goal:** Quantify environmental and financial impact.

## Milestone 4 — AI Decision

```text
Historical Data
 ↓
XGBoost
 ↓
Prediction
 ↓
Decision Engine
 ↓
On-Prem / Cloud
```

**Goal:** Make energy/carbon/cost-aware placement recommendations.

## Milestone 5 — Kubernetes Execution

```text
Decision
 ↓
Kubernetes
 ↓
On-Prem / Cloud
 ↓
Workload
```

**Goal:** Execute the placement decision for an eligible containerized workload.

---

# 22. First Build — Start Here

Do **not** start with:

```text
XGBoost
Kubernetes
AWS
Terraform
```

Start with:

```text
┌───────────────┐
│ Boiler Plate  │
└───────┬───────┘
        ▼
┌───────────────┐
│  PZEM-004T    │
└───────┬───────┘
        ▼
┌───────────────┐
│    ESP32      │
└───────┬───────┘
        │ Wi-Fi
        ▼
┌───────────────┐
│    FastAPI    │
└───────┬───────┘
        ▼
┌───────────────┐
│   InfluxDB    │
└───────┬───────┘
        ▼
┌───────────────┐
│    Grafana    │
└───────────────┘
```

### First success condition

Turn on the controlled load and see live values such as:

```text
Power:      950 W
Voltage:    230 V
Current:    4.1 A
Energy:     0.95 kWh
```

in Grafana.

Once this works, GreenColo has its first real foundation.

---

# 23. Final Mental Model

Remember the entire project as:

```text
MEASURE
   ↓
STORE
   ↓
VISUALIZE
   ↓
PREDICT
   ↓
DECIDE
   ↓
EXECUTE
   ↓
MEASURE AGAIN
```

Or:

> **PZEM tells us how much electricity we're using.**  
> **Server telemetry tells us what the workload is doing.**  
> **Electricity Maps tells us how carbon-intensive the electricity is.**  
> **The tariff tells us what it costs.**  
> **XGBoost predicts what is likely to happen.**  
> **The Decision Engine decides where an eligible workload should run.**  
> **Kubernetes executes that decision.**  
> **Grafana shows the result.**

---

# 24. Project Development Philosophy

> **Build everything with your own test setup first. When the college finally gives access, plug its real metrics into the same pipeline.**

Development progression:

```text
PZEM + ESP32 experiment
        ↓
Real-time energy monitoring
        ↓
Server/workload monitoring
        ↓
Carbon and cost analysis
        ↓
ML prediction
        ↓
AI-assisted workload placement
        ↓
Kubernetes execution
        ↓
Hybrid cloud optimization system
```

---

# 25. Immediate Next Step

### Build only this first:

```text
PZEM-004T
      ↓
ESP32
      ↓
FastAPI
      ↓
InfluxDB
      ↓
Grafana
```

After the first real-time power dashboard works, move to **server telemetry and workload correlation**.

> **Safety:** PZEM-004T involves mains electricity. The mains-side installation and testing should be handled or checked by a qualified person using appropriate isolation, enclosure, protection, and wiring practices.
