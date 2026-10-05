from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import get_settings
from backend.app.routers import health, telemetry, decision
import logging

settings = get_settings()

logging.basicConfig(
    level=logging.INFO if settings.LOG_LEVEL == "info" else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="GreenColo: Real-Time Telemetry Ingestion, Carbon Tracking, and Intelligent Workload Placement Engine"
)

# Enable CORS for local React/Grafana/Dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(telemetry.router)
app.include_router(decision.router)

@app.get("/")
def root():
    return {
        "message": "GreenColo Telemetry & Ingestion Backend is running.",
        "docs_url": "/docs",
        "health_check": "/api/v1/health",
        "telemetry_latest": "/api/v1/telemetry/latest",
        "version": settings.VERSION
    }
