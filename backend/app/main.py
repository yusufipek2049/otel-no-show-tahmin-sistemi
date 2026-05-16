from __future__ import annotations

from time import perf_counter

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger, log_event

configure_logging(level=settings.log_level)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Bootstrap API for the hotel no-show prediction system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_base_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started_at = perf_counter()
    logger.info(log_event("request_started", method=request.method, path=request.url.path))
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = int((perf_counter() - started_at) * 1000)
        logger.exception(log_event("request_failed", method=request.method, path=request.url.path, duration_ms=duration_ms))
        raise

    duration_ms = int((perf_counter() - started_at) * 1000)
    logger.info(
        log_event(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
    )
    return response


@app.get("/", tags=["meta"])
def read_root() -> dict[str, str]:
    return {
        "message": "Hotel No-Show Prediction API",
        "docs_url": "/docs",
        "health_url": f"{settings.api_v1_prefix}/health",
    }
