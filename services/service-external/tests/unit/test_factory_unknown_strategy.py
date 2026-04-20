"""Unknown adapter strategy → ValueError."""

from __future__ import annotations

import pytest

from domains.cdn_storage.adapters.factory import create_adapter as cdn_create
from domains.currency.adapters.factory import create_adapter as currency_create
from domains.maps.adapters.factory import create_adapter as maps_create
from domains.notification.adapters.factory import create_adapter as notification_create
from domains.payment.adapters.factory import create_adapter as payment_create
from domains.pms.adapters.factory import create_adapter as pms_create


@pytest.mark.parametrize(
    "factory",
    [cdn_create, currency_create, maps_create, notification_create, payment_create, pms_create],
)
def test_unknown_strategy_raises(factory):
    with pytest.raises(ValueError, match="Unknown"):
        factory("not-a-real-strategy-xyz")
