"""
Maps a service-core reservation-validate Kafka payload + PMS availability to the results topic JSON.

Used by `reservation_validate_consumer` and kept in `domains/pms` next to `AvailabilityQuery`
so behavior stays aligned with `POST /pms/v1/availability`.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from domains.pms.contracts import AvailabilityQuery
from domains.pms.ports.pms_port import PMSIntegrationPort


def build_reservation_validate_kafka_reply(
    payload: dict[str, Any],
    correlation_id: str,
    adapter: PMSIntegrationPort,
) -> dict[str, Any]:
    """Return the JSON body for `reservation-validate-results` (sync; may block on PMS)."""
    hotel_id = payload.get("hotel_id")
    check_in_raw = payload.get("check_in")
    check_out_raw = payload.get("check_out")
    room_type_id = payload.get("room_type_id")

    if not hotel_id or not check_in_raw or not check_out_raw:
        return {
            "correlation_id": correlation_id,
            "exists": False,
            "message": "PMS validate skipped: missing hotel_id or dates.",
        }

    try:
        from datetime import date

        ci = date.fromisoformat(str(check_in_raw)[:10])
        co = date.fromisoformat(str(check_out_raw)[:10])
    except ValueError:
        return {
            "correlation_id": correlation_id,
            "exists": False,
            "message": "PMS validate skipped: invalid check_in/check_out.",
        }

    nights = max((co - ci).days, 1)
    query = AvailabilityQuery(
        hotel_external_id=str(hotel_id),
        check_in=ci,
        check_out=co,
        room_type_external_id=str(room_type_id) if room_type_id else None,
    )

    try:
        slots = adapter.query_availability(query)
    except Exception as e:
        logging.exception(
            "[service-external] PMS query_availability failed correlation=%s room_type=%s",
            correlation_id[:8] if correlation_id else "",
            room_type_id,
        )
        return {
            "correlation_id": correlation_id,
            "exists": False,
            "message": f"PMS unavailable; core may fall back to local DB check. ({e})",
        }

    if not slots or len(slots) < nights:
        logging.warning(
            "[service-external] PMS returned incomplete slots (%s) for %s nights",
            len(slots) if slots else 0,
            nights,
        )
        return {
            "correlation_id": correlation_id,
            "exists": True,
            "confirmation_code": f"RES{uuid4().hex[:8].upper()}",
            "message": "PMS: incomplete or empty availability for the requested stay.",
        }

    min_units = min(s.available_units for s in slots)
    if min_units <= 0:
        return {
            "correlation_id": correlation_id,
            "exists": True,
            "confirmation_code": f"RES{uuid4().hex[:8].upper()}",
            "message": "PMS: no available units for one or more nights.",
        }

    return {
        "correlation_id": correlation_id,
        "exists": False,
        "message": "PMS: availability OK for the requested range.",
    }
