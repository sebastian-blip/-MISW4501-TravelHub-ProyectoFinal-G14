"""HTTP routes for PMS integration (driving adapter)."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TypeVar

from fastapi import APIRouter, HTTPException

from domains.pms.cached_adapter import get_cached_pms_adapter
from domains.pms.contracts import (
    AvailabilityQuery,
    PMSBookingPayload,
    WebhookRegistration,
)
from domains.pms.ports import PMSIntegrationPort

router = APIRouter()

STRATEGY = os.getenv("PMS_ADAPTER_STRATEGY", "pms")

T = TypeVar("T")


def get_adapter() -> PMSIntegrationPort:
    return get_cached_pms_adapter()


def _run_pms(fn: Callable[[], T]) -> T:
    try:
        return fn()
    except RuntimeError as e:
        if "circuit_open" in str(e):
            raise HTTPException(status_code=503, detail=str(e)) from e
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail="upstream_pms_error") from e


@router.get("/v1/catalog/{hotel_external_id}")
def get_catalog(hotel_external_id: str):
    def _go():
        return get_adapter().fetch_catalog_snapshot(hotel_external_id).model_dump(mode="json")

    return _run_pms(_go)


@router.post("/v1/availability")
def post_availability(query: AvailabilityQuery):
    """Query nightly availability and rates for a stay window."""

    def _go():
        slots = get_adapter().query_availability(query)
        return [s.model_dump(mode="json") for s in slots]

    return _run_pms(_go)


@router.post("/v1/bookings/confirmation")
def post_booking_confirmation(payload: PMSBookingPayload):
    """Push a booking confirmation to the PMS (idempotent where supported)."""

    def _go():
        get_adapter().push_booking_confirmation(payload)
        return {"status": "accepted"}

    return _run_pms(_go)


@router.post("/v1/webhooks/inventory")
def post_inventory_webhook(registration: WebhookRegistration):
    """Register a callback URL for PMS inventory change notifications."""

    def _go():
        webhook_id = get_adapter().register_inventory_webhook(registration)
        return {"webhook_id": webhook_id}

    return _run_pms(_go)


def strategy_label() -> str:
    return STRATEGY
