"""Unit tests for reservation-validate Kafka handler (mock producer)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

import infrastructure.messaging.kafka.reservation_validate_consumer as mod
from infrastructure.messaging.kafka.topics import TOPIC_RESERVATION_RESULTS


@pytest.mark.asyncio
async def test_handle_publishes_exists_false_when_random_high():
    mock_producer = AsyncMock()
    mod._producer = mock_producer

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
async def test_handle_publishes_exists_true_when_random_low():
    mock_producer = AsyncMock()
    mod._producer = mock_producer

    with patch.object(mod.random, "random", return_value=0.0):
        await mod._handle({"correlation_id": "corr-aaaa-bbbb"})

    mock_producer.send_and_wait.assert_called_once()
    body = json.loads(mock_producer.send_and_wait.call_args[0][1].decode())
    assert body["exists"] is True
    assert body["correlation_id"] == "corr-aaaa-bbbb"
    assert body["confirmation_code"].startswith("RES")
