"""Maps/Location — hexagonal HTTP entry-point (driving adapter)."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from app.ports import LocationPort
from app.adapters import create_adapter
from service_external.contracts.location import GeocodeRequest

app = FastAPI(title="TravelHub Maps", version="0.1.0")
_adapter: LocationPort | None = None

ADAPTER_STRATEGY = os.getenv("ADAPTER_STRATEGY", "maps")


def get_adapter() -> LocationPort:
    global _adapter
    if _adapter is None:
        _adapter = create_adapter(ADAPTER_STRATEGY)
    return _adapter


@app.get("/health")
def health():
    return {"status": "ok", "service": "maps", "strategy": ADAPTER_STRATEGY}


@app.get("/ready")
def ready():
    return {"ready": True}


@app.get("/v1/geocode")
def geocode(address_line: str, city: str, country_code: str):
    try:
        req = GeocodeRequest(address_line=address_line, city=city, country_code=country_code.upper()[:2])
        return get_adapter().geocode(req).model_dump()
    except RuntimeError as e:
        if "circuit_open" in str(e):
            raise HTTPException(status_code=503, detail=str(e)) from e
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail="upstream_maps_error") from e
