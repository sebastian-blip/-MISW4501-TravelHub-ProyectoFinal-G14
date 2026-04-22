from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class PMSCatalogSnapshot(BaseModel):
    hotel_external_id: str
    property_name: str
    room_types: list[dict]


class AvailabilityQuery(BaseModel):
    hotel_external_id: str
    check_in: date
    check_out: date
    room_type_external_id: str | None = Field(
        default=None,
        description="Optional room/product id for PMS adapters that support per-room availability.",
    )


class AvailabilitySlot(BaseModel):
    date: date
    available_units: int
    rate: Decimal
    currency: str


class PMSBookingPayload(BaseModel):
    external_booking_id: str = ""
    hotel_external_id: str = ""
    guest_email: str | None = None


class WebhookRegistration(BaseModel):
    hotel_external_id: str
    callback_url: str


class WebhookRegistrationResult(BaseModel):
    webhook_id: str
