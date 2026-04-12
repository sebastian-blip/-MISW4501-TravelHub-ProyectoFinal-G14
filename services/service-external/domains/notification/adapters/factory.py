from __future__ import annotations

from domains.notification.ports.notification_port import NotificationPort

_STRATEGIES: dict[str, type] = {}


def _load_strategies() -> dict[str, type]:
    if _STRATEGIES:
        return _STRATEGIES
    from domains.notification.adapters.email_sms_adapter import EmailSmsAdapter
    from domains.notification.adapters.mock_adapter import MockNotificationAdapter

    _STRATEGIES["email_sms"] = EmailSmsAdapter
    _STRATEGIES["mock"] = MockNotificationAdapter
    return _STRATEGIES


def create_adapter(strategy: str) -> NotificationPort:
    strategies = _load_strategies()
    cls = strategies.get(strategy)
    if cls is None:
        available = ", ".join(sorted(strategies))
        raise ValueError(f"Unknown notification strategy '{strategy}'. Available: {available}")
    return cls()
