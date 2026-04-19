"""
Kafka reservation-validate consumer + `build_reservation_validate_kafka_reply`.

PMS mode uses the same cached adapter and availability rules as `POST /pms/v1/availability`
(see `domains.pms.reservation_validate_reply`). Random mode is for chaos/tests only.
"""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

import infrastructure.messaging.kafka.reservation_validate_consumer as mod
from domains.pms.adapters.mock_adapter import MockPMSAdapter
from domains.pms.contracts import AvailabilityQuery, AvailabilitySlot
from domains.pms.reservation_validate_reply import build_reservation_validate_kafka_reply
from infrastructure.messaging.kafka.topics import TOPIC_RESERVATION_RESULTS


@pytest.mark.asyncio
async def test_handle_random_mode_exists_false():
    mock_producer = AsyncMock()
    mod._producer = mock_producer

    with patch.object(mod, "_use_random_validate", return_value=True):
        with patch.object(mod, "_EXISTS_RATE", 0.5):
            with patch.object(mod.random, "random", return_value=0.99):
                await mod._handle(
                    {
                        "correlation_id": "corr-1111-2222",
                        "hotel_id": "h1",
                    }
                )

    mock_producer.send_and_wait.assert_called_once()
    topic, payload = mock_producer.send_and_wait.call_args[0]
    assert topic == TOPIC_RESERVATION_RESULTS
    body = json.loads(payload.decode())
    assert body["correlation_id"] == "corr-1111-2222"
    assert body["exists"] is False
    assert "message" in body


@pytest.mark.asyncio
async def test_handle_random_mode_exists_true():
    mock_producer = AsyncMock()
    mod._producer = mock_producer

    with patch.object(mod, "_use_random_validate", return_value=True):
        with patch.object(mod, "_EXISTS_RATE", 0.5):
            with patch.object(mod.random, "random", return_value=0.0):
                await mod._handle({"correlation_id": "corr-aaaa-bbbb"})

    mock_producer.send_and_wait.assert_called_once()
    body = json.loads(mock_producer.send_and_wait.call_args[0][1].decode())
    assert body["exists"] is True
    assert body["correlation_id"] == "corr-aaaa-bbbb"
    assert body["confirmation_code"].startswith("RES")


class _PmsOk:
    def query_availability(self, query: AvailabilityQuery):
        n = max((query.check_out - query.check_in).days, 1)
        return [
            AvailabilitySlot(
                date=query.check_in + timedelta(days=i),
                available_units=5,
                rate=Decimal("100"),
                currency="USD",
            )
            for i in range(n)
        ]


@pytest.mark.asyncio
async def test_handle_pms_mode_availability_ok():
    mock_producer = AsyncMock()
    mod._producer = mock_producer

    with patch.object(mod, "_use_random_validate", return_value=False):
        with patch(
            "infrastructure.messaging.kafka.reservation_validate_consumer.get_cached_pms_adapter",
            return_value=_PmsOk(),
        ):
            await mod._handle(
                {
                    "correlation_id": "c-pms-1",
                    "hotel_id": "b1000000-0000-0000-0000-000000000001",
                    "check_in": "2030-01-01",
                    "check_out": "2030-01-04",
                }
            )

    body = json.loads(mock_producer.send_and_wait.call_args[0][1].decode())
    assert body["exists"] is False
    assert "PMS" in body["message"]


class _PmsNoUnits:
    def query_availability(self, query: AvailabilityQuery):
        n = max((query.check_out - query.check_in).days, 1)
        return [
            AvailabilitySlot(
                date=query.check_in + timedelta(days=i),
                available_units=0 if i == 0 else 3,
                rate=Decimal("100"),
                currency="USD",
            )
            for i in range(n)
        ]


@pytest.mark.asyncio
async def test_handle_pms_mode_zero_units():
    mock_producer = AsyncMock()
    mod._producer = mock_producer

    with patch.object(mod, "_use_random_validate", return_value=False):
        with patch(
            "infrastructure.messaging.kafka.reservation_validate_consumer.get_cached_pms_adapter",
            return_value=_PmsNoUnits(),
        ):
            await mod._handle(
                {
                    "correlation_id": "c-pms-2",
                    "hotel_id": "hotel-x",
                    "check_in": "2030-02-01",
                    "check_out": "2030-02-03",
                }
            )

    body = json.loads(mock_producer.send_and_wait.call_args[0][1].decode())
    assert body["exists"] is True
    assert "confirmation_code" in body


class TestBuildReservationValidateKafkaReply:
    """Same logic path as HTTP availability + core Kafka reply shape."""

    def test_missing_hotel_or_dates_skipped(self):
        out = build_reservation_validate_kafka_reply({}, "cid", _PmsOk())
        assert out["exists"] is False
        assert "skipped" in out["message"].lower()

    def test_invalid_dates_skipped(self):
        out = build_reservation_validate_kafka_reply(
            {
                "hotel_id": "h1",
                "check_in": "not-a-date",
                "check_out": "2030-01-02",
            },
            "cid",
            _PmsOk(),
        )
        assert out["exists"] is False
        assert "invalid" in out["message"].lower()

    def test_adapter_exception_allows_core_db_fallback(self):
        class _Boom:
            def query_availability(self, query: AvailabilityQuery):
                raise RuntimeError("pms down")

        out = build_reservation_validate_kafka_reply(
            {
                "hotel_id": "h1",
                "check_in": "2030-01-01",
                "check_out": "2030-01-03",
            },
            "cid",
            _Boom(),
        )
        assert out["exists"] is False
        assert "PMS unavailable" in out["message"]
        assert "pms down" in out["message"]

    def test_incomplete_slots_treated_as_blocked(self):
        class _Short:
            def query_availability(self, query: AvailabilityQuery):
                return [
                    AvailabilitySlot(
                        date=query.check_in,
                        available_units=5,
                        rate=Decimal("1"),
                        currency="USD",
                    )
                ]

        out = build_reservation_validate_kafka_reply(
            {
                "hotel_id": "h1",
                "check_in": "2030-01-01",
                "check_out": "2030-01-05",
            },
            "cid",
            _Short(),
        )
        assert out["exists"] is True
        assert "incomplete" in out["message"].lower()

    def test_with_mock_pms_adapter_matches_four_night_stay(self):
        adapter = MockPMSAdapter()
        out = build_reservation_validate_kafka_reply(
            {
                "hotel_id": "hotel-ext-001",
                "room_type_id": "std",
                "check_in": "2030-06-01",
                "check_out": "2030-06-05",
            },
            "corr-z",
            adapter,
        )
        assert out["correlation_id"] == "corr-z"
        assert out["exists"] is False
        assert "OK" in out["message"]

    def test_passes_room_type_id_to_query(self):
        seen: list[AvailabilityQuery] = []

        class _Capture(_PmsOk):
            def query_availability(self, query: AvailabilityQuery):
                seen.append(query)
                return super().query_availability(query)

        build_reservation_validate_kafka_reply(
            {
                "hotel_id": "h1",
                "room_type_id": "room-uuid-1",
                "check_in": "2030-01-01",
                "check_out": "2030-01-03",
            },
            "cid",
            _Capture(),
        )
        assert len(seen) == 1
        assert seen[0].room_type_external_id == "room-uuid-1"
        assert seen[0].hotel_external_id == "h1"
