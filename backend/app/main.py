import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app import config
from app.database import SessionLocal
from app.routers import tickets
from app.seed import seed_demo_data

logger = logging.getLogger("helpdesk")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if config.SEED_DEMO_DATA:
        with SessionLocal() as db:
            logger.info("seeded %s demo tasks", seed_demo_data(db))
    yield


app = FastAPI(title="HelpDesk API", version=config.APP_VERSION, lifespan=lifespan)

if config.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"]
    )

app.include_router(tickets.router)


@app.get("/", tags=["system"])
def root():
    return {
        "service": "helpdesk-backend",
        "version": config.APP_VERSION,
        "environment": config.ENVIRONMENT,
        "docs": "/docs",
    }


@app.get("/health", tags=["system"])
def health():
    """Liveness: the process is up. Deliberately does not touch the database."""
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
def ready():
    """Readiness: the application can serve traffic, i.e. the database answers."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - any DB failure means "not ready"
        logger.warning("readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "READY"}


Instrumentator(excluded_handlers=["/metrics", "/health", "/ready"]).instrument(app).expose(
    app, endpoint="/metrics", include_in_schema=False
)
