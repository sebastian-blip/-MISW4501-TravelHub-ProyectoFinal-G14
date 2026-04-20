"""Normalize currency codes for FX providers (USDC treated as USD for rates)."""

from __future__ import annotations

import re

_CCY = re.compile(r"^(USDC|[A-Z]{3})$")


def validate_display_currency(code: str) -> str:
    """Return stripped uppercase code: ISO 4217 (3 letters) or USDC."""
    u = (code or "").strip().upper()
    if not _CCY.match(u):
        raise ValueError("currency must be USDC or a 3-letter ISO code")
    return u


def fx_provider_code(code: str) -> str:
    """Map to the symbol sent to FX APIs (Frankfurter has no USDC)."""
    v = validate_display_currency(code)
    return "USD" if v == "USDC" else v
