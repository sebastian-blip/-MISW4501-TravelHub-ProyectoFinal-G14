"""Integration slices: **ports** (ABC) + **adapters** (driven side) per provider.

This is not the DDD "domain core" (entities/agregados). Here each subpackage is a
**bounded integration** (PMS, payment, …): the port faces inward; adapters implement
outbound calls (HTTP, mocks, etc.). HTTP lives in ``app.routes`` (driving adapters).
"""
