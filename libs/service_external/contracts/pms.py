from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PMSCatalogSnapshot(BaseModel):
    hotel_external_id: str
    property_name: str
    room_types: list[dict] = Field(default_factory=list)


class AvailabilityQuery(BaseModel):
    hotel_external_id: str
    check_in: date
    check_out: date
    room_type_external_id: str | None = None


class AvailabilitySlot(BaseModel):
    date: date
    available_units: int
    rate: Decimal | None = None
    currency: str | None = None


class PMSBookingPayload(BaseModel):
    reservation_id: UUID
    hotel_external_id: str
    guest_name: str
    check_in: date
    check_out: date
    external_confirmation_code: str | None = None


class WebhookRegistration(BaseModel):
    callback_url: str
    secret: str
    events: list[str] = Field(default_factory=lambda: ["inventory.updated", "rates.updated"])
