"""
Tests unitarios para el router de pruebas AWS/Kafka.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from routes.test_router import router as test_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(test_router)
    return TestClient(app)


class TestTestRouter:
    """Tests para /test"""

    def test_kafka_aws_success(self, client):
        """Test envío de mensaje de prueba a Kafka exitoso."""
        with patch("routes.test_router.publish_test_message") as mock_publish:
            response = client.post("/test/kafka-aws", json={
                "message": "Test de conectividad",
                "priority": "high",
                "metadata": {"region": "us-east-1", "test_id": "123"}
            })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message_sent"] == "Test de conectividad"
        assert data["details"]["priority"] == "high"
        assert data["details"]["target_topic"] == "aws-test-messages"
        mock_publish.assert_called_once()

    def test_kafka_aws_default_values(self, client):
        """Test envío de mensaje con valores por defecto."""
        with patch("routes.test_router.publish_test_message") as mock_publish:
            response = client.post("/test/kafka-aws", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message_sent"] == "Ping desde service-core"
        assert data["details"]["priority"] == "normal"
        mock_publish.assert_called_once()

    def test_kafka_aws_error(self, client):
        """Test envío de mensaje falla cuando Kafka no está disponible."""
        with patch("routes.test_router.publish_test_message", side_effect=Exception("Kafka no disponible")):
            response = client.post("/test/kafka-aws", json={
                "message": "Test fallido",
            })

        assert response.status_code == 500
        assert "Kafka" in response.json()["detail"]

    def test_kafka_health(self, client):
        """Test health check del endpoint de test."""
        response = client.get("/test/kafka-aws/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "service-core"
        assert data["status"] == "ok"
        assert data["kafka_enabled"] is True
        assert data["test_endpoint_available"] is True
        assert "timestamp" in data
