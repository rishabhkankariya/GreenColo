from fastapi import APIRouter
from backend.app.config import get_settings
from backend.app.services.influx_service import influx_service
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1", tags=["Health"])

@router.get("/health")
def health_check():
    settings = get_settings()
    influx_ok = influx_service.is_healthy()
    return {
        "status": "healthy" if influx_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "influxdb_connected": influx_ok,
        "carbon_mock_mode": settings.USE_MOCK_CARBON,
        "zone": settings.ELECTRICITY_MAPS_ZONE,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
