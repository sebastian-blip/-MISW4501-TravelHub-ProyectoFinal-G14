"""Unit tests for Kafka client config helpers."""

from __future__ import annotations

from infrastructure.messaging.kafka._kafka_config import (
    consumer_base_config,
    producer_base_config,
)


def test_consumer_base_config_plaintext_when_no_credentials(monkeypatch):
    monkeypatch.delenv("KAFKA_USERNAME", raising=False)
    monkeypatch.delenv("KAFKA_PASSWORD", raising=False)

    cfg = consumer_base_config("localhost:9092", "g1")

    assert cfg["bootstrap_servers"] == "localhost:9092"
    assert cfg["group_id"] == "g1"
    assert "sasl_mechanism" not in cfg


def test_consumer_base_config_sasl_when_credentials(monkeypatch):
    monkeypatch.setenv("KAFKA_USERNAME", "user")
    monkeypatch.setenv("KAFKA_PASSWORD", "secret")

    cfg = consumer_base_config("kafka:9092", "my-group")

    assert cfg["sasl_mechanism"] == "SCRAM-SHA-256"
    assert cfg["security_protocol"] == "SASL_PLAINTEXT"
    assert cfg["sasl_plain_username"] == "user"
    assert cfg["sasl_plain_password"] == "secret"


def test_producer_base_config_plaintext_when_no_credentials(monkeypatch):
    monkeypatch.delenv("KAFKA_USERNAME", raising=False)
    monkeypatch.delenv("KAFKA_PASSWORD", raising=False)

    cfg = producer_base_config("localhost:9092")

    assert cfg == {"bootstrap_servers": "localhost:9092"}


def test_producer_base_config_sasl_when_credentials(monkeypatch):
    monkeypatch.setenv("KAFKA_USERNAME", "u")
    monkeypatch.setenv("KAFKA_PASSWORD", "p")

    cfg = producer_base_config("b1:9092")

    assert cfg["bootstrap_servers"] == "b1:9092"
    assert cfg["sasl_mechanism"] == "SCRAM-SHA-256"
