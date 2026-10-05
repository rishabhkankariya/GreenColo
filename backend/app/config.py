from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "GreenColo Telemetry & Ingestion API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"

    # InfluxDB
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "greencolo-super-secret-admin-token-2026"
    INFLUXDB_ORG: str = "greencolo"
    INFLUXDB_BUCKET: str = "greencolo_telemetry"

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "greencolo_db"
    POSTGRES_USER: str = "greencolo_admin"
    POSTGRES_PASSWORD: str = "greencolo_secure_pass_2026"

    # Electricity Maps / Carbon
    ELECTRICITY_MAPS_API_KEY: Optional[str] = None
    ELECTRICITY_MAPS_ZONE: str = "IN-WE"
    USE_MOCK_CARBON: bool = True

    # Regional Tariff (MSEDCL Baseline in INR per kWh)
    DEFAULT_TARIFF_INR_PER_KWH: float = 11.50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
