"""Pytest hooks for service-external.

Kafka is disabled before any test imports `main`, so lifespan does not connect
to a broker during unit tests.
"""
import os

os.environ["KAFKA_ENABLED"] = "false"
os.environ["KAFKA_BOOTSTRAP_SERVERS"] = ""

# HTTP integration routes use mock adapters (no real gateway/PMS calls in unit tests).
os.environ["PAYMENT_ADAPTER_STRATEGY"] = "mock"
os.environ["PMS_ADAPTER_STRATEGY"] = "mock"
os.environ["CURRENCY_ADAPTER_STRATEGY"] = "mock"
