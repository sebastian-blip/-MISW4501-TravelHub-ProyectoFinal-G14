"""Unit tests for booking consumer helpers (currency normalization)."""

from __future__ import annotations

import pytest

from infrastructure.messaging.kafka.booking_integration_consumer import _normalize_currency


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("USD", "USD"),
        ("usd", "USD"),
        ("  eur  ", "EUR"),
        ("XX", "USD"),
        ("", "USD"),
    ],
)
def test_normalize_currency(raw, expected):
    assert _normalize_currency(raw) == expected
