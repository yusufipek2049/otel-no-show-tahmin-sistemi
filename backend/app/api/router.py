from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import actions, dashboard, health, reports, reservations

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["reservations"])
api_router.include_router(actions.router, prefix="/actions", tags=["actions"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
