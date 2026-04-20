"""Kafka lifecycle + reservation consumer edge cases."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

import infrastructure.messaging.kafka.lifecycle as lifecycle_mod
import infrastructure.messaging.kafka.reservation_validate_consumer as consumer_mod


@pytest.mark.asyncio
async def test_start_kafka_consumers_skips_when_disabled(caplog):
    with patch.dict("os.environ", {"TH_CONSUME_RESERVATION_VALIDATE": "false"}, clear=False):
        with caplog.at_level("INFO"):
            await lifecycle_mod.start_kafka_consumers("localhost:9092")
    assert any("TH_CONSUME_RESERVATION_VALIDATE=false" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_start_kafka_consumers_awaits_reservation_consumer():
    with patch.dict("os.environ", {"TH_CONSUME_RESERVATION_VALIDATE": "true"}, clear=False):
        with patch(
            "infrastructure.messaging.kafka.lifecycle.start_reservation_validate_consumer",
            new_callable=AsyncMock,
        ) as m:
            await lifecycle_mod.start_kafka_consumers("broker:9092")
    m.assert_awaited_once_with("broker:9092")


@pytest.mark.asyncio
async def test_stop_kafka_consumers_awaits_reservation_stop():
    with patch(
        "infrastructure.messaging.kafka.lifecycle.stop_reservation_validate_consumer",
        new_callable=AsyncMock,
    ) as m:
        await lifecycle_mod.stop_kafka_consumers()
    m.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_reservation_validate_consumer_idempotent():
    mod = consumer_mod
    mod._consumer = object()
    mod._producer = object()
    mod._task = None
    try:
        await mod.start_reservation_validate_consumer("localhost:9092")
    finally:
        mod._consumer = None
        mod._producer = None
        mod._task = None


@pytest.mark.asyncio
async def test_stop_reservation_validate_consumer_when_nothing_running():
    mod = consumer_mod
    mod._consumer = None
    mod._producer = None
    mod._task = None
    await mod.stop_reservation_validate_consumer()


@pytest.mark.asyncio
async def test_consume_loop_swallows_cancelled_error():
    class FakeConsumer:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise asyncio.CancelledError()

    consumer_mod._consumer = FakeConsumer()
    await consumer_mod._consume_loop()
    consumer_mod._consumer = None
