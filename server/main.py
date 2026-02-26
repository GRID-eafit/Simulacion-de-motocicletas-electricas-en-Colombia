"""
Application entry point.

Creates the FastAPI instance, attaches CORS middleware, and registers all
routers from the app package.  Business logic lives in app/api/routers/,
app/services/, app/models/, and app/utils/ — not here.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routers import (
    costs_router,
    fleet_router,
    misc_router,
    routes_router,
    tiles_router,
)

app = FastAPI(
    title="Simulación de Motocicletas Eléctricas en Colombia",
    description=(
        "API for simulating electric motorcycle routes, energy consumption, "
        "fleet optimisation and trip cost estimation."
    ),
    version="1.0.0",
)

# Middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers

app.include_router(misc_router.router)
app.include_router(routes_router.router)
app.include_router(fleet_router.router)
app.include_router(costs_router.router)
app.include_router(tiles_router.router)
