"""
Tests unitarios para el router de health check.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.health_router import router as health_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(health_router)
    return TestClient(app)


class TestHealthRouter:
    """Tests para /health"""

    def test_health_check(self, client):
        """Test health check retorna status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "user-service"
