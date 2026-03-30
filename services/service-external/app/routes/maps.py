"""HTTP routes for maps / geocoding (driving adapter)."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from app.domains.maps.adapters import create_adapter
from app.domains.maps.ports import LocationPort
from service_external.contracts.location import GeocodeRequest

router = APIRouter()
_adapter: LocationPort | None = None

STRATEGY = os.getenv("MAPS_ADAPTER_STRATEGY", "maps")


def get_adapter() -> LocationPort:
    global _adapter
    if _adapter is None:
        _adapter = create_adapter(STRATEGY)
    return _adapter


@router.get("/v1/geocode")
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


def strategy_label() -> str:
    return STRATEGY
