"""TravelHub — single external-integrations HTTP service."""

from __future__ import annotations

import os

from fastapi import FastAPI

from app.routes import integration_strategies, mount_routes

app = FastAPI(title="TravelHub Service External", version="0.1.0")
mount_routes(app)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "service-external",
        "integrations": integration_strategies(),
    }


@app.get("/ready")
def ready():
    if os.getenv("TH_PAYMENT_SKIP_READY", "").lower() in ("1", "true", "yes"):
        return {"ready": True, "skipped": True}
    return {"ready": True}
