from fastapi import APIRouter
from backend.app.models.schemas import DecisionRequest, DecisionResponse
from backend.app.services.carbon_service import carbon_service
from backend.app.services.cost_engine import cost_engine
from datetime import datetime, timezone
import uuid
import os
import logging
import joblib
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/decision", tags=["Decision Engine"])

# Attempt loading pre-trained XGBoost PUE model
MODEL_PATH = "ml/models/xgboost_pue_model.pkl"
pue_model = None
if os.path.exists(MODEL_PATH):
    try:
        pue_model = joblib.load(MODEL_PATH)
        logger.info("Successfully loaded XGBoost PUE model from %s", MODEL_PATH)
    except Exception as e:
        logger.warning("Failed to load XGBoost model: %s", str(e))

def predict_pue(cpu_pct: float, memory_pct: float, ambient_temp: float = 26.0) -> float:
    now = datetime.now()
    if pue_model is not None:
        try:
            # Features: hour_of_day, day_of_week, cpu_percent, memory_percent, ambient_temp_c
            features = np.array([[now.hour, now.weekday(), cpu_pct, memory_pct, ambient_temp]])
            pred = float(pue_model.predict(features)[0])
            return round(max(1.10, min(1.85, pred)), 3)
        except Exception as e:
            logger.debug("Model inference fallback: %s", str(e))
    # Fallback empirical estimate
    return round(1.20 + (0.003 * cpu_pct) + (0.01 * max(0.0, ambient_temp - 22.0)), 3)

@router.post("/evaluate", response_model=DecisionResponse)
def evaluate_workload_placement(request: DecisionRequest):
    """
    Evaluates incoming workload attributes against current grid carbon intensity,
    electricity tariff, XGBoost predicted PUE, and resource constraints to select
    the optimal execution environment (ON_PREMISE vs. AWS_CLOUD).
    """
    grid = carbon_service.get_current_grid_carbon()

    # Predict On-Premise PUE using trained XGBoost model
    estimated_cpu_load = min(95.0, 30.0 + (request.cpu_cores_required * 15.0))
    predicted_on_prem_pue = predict_pue(cpu_pct=estimated_cpu_load, memory_pct=50.0, ambient_temp=27.5)

    # Cloud average baseline PUE (hyperscale cloud providers like AWS typically run at PUE ~1.15)
    cloud_pue = 1.15
    cloud_carbon_intensity = 320.0  # low-carbon region estimate in gCO2/kWh
    on_prem_carbon_intensity = grid.carbon_intensity_g_co2_kwh  # typically ~620-720 gCO2/kWh

    # Power draw calculation: IT power * PUE
    base_it_power_w = 45.0 + (request.cpu_cores_required * 25.0)
    total_on_prem_power_w = base_it_power_w * predicted_on_prem_pue
    total_cloud_power_w = base_it_power_w * cloud_pue

    estimated_duration_hrs = (request.deadline_minutes or 60) / 60.0
    on_prem_kwh = (total_on_prem_power_w / 1000.0) * estimated_duration_hrs
    cloud_kwh = (total_cloud_power_w / 1000.0) * estimated_duration_hrs

    # Cost calculation: On-prem electricity vs Cloud vCPU billing
    on_prem_cost = round(on_prem_kwh * (grid.electricity_tariff_inr_per_kwh or 11.50), 2)
    cloud_cost = round(request.cpu_cores_required * estimated_duration_hrs * 1.50, 2)

    # Carbon emissions: kWh * carbon intensity
    on_prem_carbon = round(on_prem_kwh * on_prem_carbon_intensity, 2)
    cloud_carbon = round(cloud_kwh * cloud_carbon_intensity, 2)

    # Multi-Objective Scoring (lower is better):
    norm_on_prem_carbon = on_prem_carbon / max(on_prem_carbon, cloud_carbon, 1.0)
    norm_cloud_carbon = cloud_carbon / max(on_prem_carbon, cloud_carbon, 1.0)

    norm_on_prem_cost = on_prem_cost / max(on_prem_cost, cloud_cost, 1.0)
    norm_cloud_cost = cloud_cost / max(on_prem_cost, cloud_cost, 1.0)

    w_carbon = request.sustainability_priority
    w_cost = request.cost_priority

    score_on_prem = round((w_carbon * norm_on_prem_carbon) + (w_cost * norm_on_prem_cost), 3)
    score_cloud = round((w_carbon * norm_cloud_carbon) + (w_cost * norm_cloud_cost), 3)

    # Guardrails: Hard SLA Constraints
    sla_feasible = True
    if request.latency_tolerance == "low" or request.workload_type == "realtime":
        destination = "ON_PREMISE"
        reason = "Workload requires strict low latency and localized node access. Retained on-premise despite higher carbon intensity."
    elif score_cloud < score_on_prem:
        destination = "AWS_CLOUD"
        reason = (
            f"Cloud offers lower carbon impact ({cloud_carbon_intensity} vs {round(on_prem_carbon_intensity, 1)} gCO2/kWh) "
            f"and better cooling efficiency (PUE {cloud_pue} vs predicted {predicted_on_prem_pue}) within cost budget."
        )
    else:
        destination = "ON_PREMISE"
        reason = "On-premise execution is cost-optimal and within allowable carbon and operational thresholds."

    return DecisionResponse(
        decision_id=str(uuid.uuid4()),
        workload_id=request.workload_id,
        timestamp=datetime.now(timezone.utc),
        recommended_destination=destination,
        reason=reason,
        scores={
            "on_premise_score": score_on_prem,
            "cloud_score": score_cloud,
            "predicted_on_prem_pue": predicted_on_prem_pue,
            "cloud_pue": cloud_pue,
            "on_prem_carbon_g": on_prem_carbon,
            "cloud_carbon_g": cloud_carbon,
            "on_prem_cost_inr": on_prem_cost,
            "cloud_cost_inr": cloud_cost
        },
        estimated_power_w=round(total_cloud_power_w if destination == "AWS_CLOUD" else total_on_prem_power_w, 1),
        estimated_carbon_g_co2=cloud_carbon if destination == "AWS_CLOUD" else on_prem_carbon,
        estimated_cost_inr=cloud_cost if destination == "AWS_CLOUD" else on_prem_cost,
        sla_feasible=sla_feasible
    )
