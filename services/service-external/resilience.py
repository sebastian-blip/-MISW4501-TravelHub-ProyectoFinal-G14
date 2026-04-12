from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5) -> None:
        self.failure_threshold = failure_threshold
        self._failures = 0

    def allow(self) -> bool:
        return self._failures < self.failure_threshold

    def record_success(self) -> None:
        self._failures = 0

    def record_failure(self) -> None:
        self._failures += 1


def retry_with_backoff(
    fn: Callable[[], T],
    max_attempts: int = 3,
    base_delay: float = 1.0,
) -> T:
    last: BaseException | None = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except BaseException as e:
            last = e
            if attempt == max_attempts - 1:
                raise
            time.sleep(base_delay * (2**attempt))
    assert last is not None
    raise last
