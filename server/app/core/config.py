"""
Centralised application settings loaded from environment variables / .env file.

Usage:
    from app.core.config import settings
    token = settings.ORS_TOKEN
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # External API tokens
    ORS_TOKEN: str = os.getenv("ORS_TOKEN", "")
    AZURE_TOKEN: str = os.getenv("AZURE_TOKEN", "")

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    ]

    # Server port (informational – used by Dockerfile / uvicorn CLI)
    PORT: int = int(os.getenv("PORT", "8000"))

    # Gurobi / fleet optimizer credentials
    WLSACCESSID: str = os.getenv("WLSACCESSID", "")
    WLSSECRET: str = os.getenv("WLSSECRET", "")
    LICENSEID: int = int(os.getenv("LICENSEID", "0"))


settings = Settings()
