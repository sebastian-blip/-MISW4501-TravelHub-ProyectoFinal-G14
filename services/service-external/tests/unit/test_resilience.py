"""Coverage for `resilience` (circuit breaker + retry)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from resilience import CircuitBreaker, retry_with_backoff


def test_circuit_breaker_allow_and_reset_on_success():
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.allow() is True
    cb.record_failure()
    cb.record_failure()
    assert cb.allow() is True
    cb.record_success()
    assert cb._failures == 0
    assert cb.allow() is True


def test_circuit_breaker_blocks_after_threshold():
    cb = CircuitBreaker(failure_threshold=2)
    cb.record_failure()
    assert cb.allow() is True
    cb.record_failure()
    assert cb.allow() is False


def test_retry_succeeds_first_attempt():
    calls: list[int] = []

    def fn():
        calls.append(1)
        return "ok"

    assert retry_with_backoff(fn, max_attempts=3) == "ok"
    assert calls == [1]


def test_retry_recovers_after_failures():
    n = {"i": 0}

    def fn():
        n["i"] += 1
        if n["i"] < 2:
            raise ConnectionError("transient")
        return "recovered"

    with patch("resilience.time.sleep"):
        assert retry_with_backoff(fn, max_attempts=3, base_delay=0.01) == "recovered"
    assert n["i"] == 2


def test_retry_exhausts_and_raises_last_error():
    def fn():
        raise ValueError("always")

    with patch("resilience.time.sleep"):
        with pytest.raises(ValueError, match="always"):
            retry_with_backoff(fn, max_attempts=2, base_delay=0.01)
