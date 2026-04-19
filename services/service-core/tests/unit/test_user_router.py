"""
Tests unitarios para el router de usuarios.
"""
import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from routes.user_router import router as user_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(user_router)
    return TestClient(app)


class TestUserRouter:
    """Tests para /users"""

    def test_get_user_by_id_success(self, client):
        """Test obtener usuario por ID exitoso."""
        user_id = "a2000000-0000-0000-0000-000000000001"
        mock_response = {
            "id": user_id,
            "email": "test@example.com",
            "first_name": "Juan",
            "last_name": "Pérez",
            "phone": "+573001234567",
            "country_id": "a1000000-0000-0000-0000-000000000001",
            "user_type": "traveler",
            "email_verified": True,
            "mfa_enabled": False,
            "active": True,
        }

        with patch("routes.user_router.Mediator.send", new_callable=AsyncMock, return_value=mock_response):
            response = client.get(f"/users/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Juan"

    def test_get_user_by_id_not_found(self, client):
        """Test obtener usuario por ID inexistente retorna 404."""
        user_id = "a2000000-0000-0000-0000-000000000999"

        with patch("routes.user_router.Mediator.send", new_callable=AsyncMock, side_effect=ValueError("Usuario no encontrado")):
            response = client.get(f"/users/{user_id}")

        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]

    def test_get_user_by_email_success(self, client):
        """Test obtener usuario por email exitoso."""
        mock_response = {
            "id": "a2000000-0000-0000-0000-000000000001",
            "email": "test@example.com",
            "first_name": "Juan",
            "last_name": "Pérez",
            "phone": None,
            "country_id": None,
            "user_type": "traveler",
            "email_verified": False,
            "mfa_enabled": False,
            "active": True,
        }

        with patch("routes.user_router.Mediator.send", new_callable=AsyncMock, return_value=mock_response):
            response = client.get("/users?email=test@example.com")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Juan"

    def test_get_user_by_email_not_found(self, client):
        """Test obtener usuario por email inexistente retorna 404."""
        with patch("routes.user_router.Mediator.send", new_callable=AsyncMock, side_effect=ValueError("Usuario no encontrado")):
            response = client.get("/users?email=notfound@example.com")

        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]

    def test_get_user_invalid_uuid(self, client):
        """Test obtener usuario con UUID inválido retorna 422."""
        response = client.get("/users/not-a-uuid")
        assert response.status_code == 422
