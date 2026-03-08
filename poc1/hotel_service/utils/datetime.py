from __future__ import annotations

from datetime import datetime, timezone


def ensure_utc(dt: datetime | None = None) -> datetime:
    """Garantiza un datetime consciente y en UTC."""

    if dt is None:
        return datetime.now(tz=timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
