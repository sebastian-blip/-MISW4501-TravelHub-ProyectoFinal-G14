"""
Tests unitarios para el router de autenticación.
"""
import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from routes.auth_router import router as auth_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(auth_router)
    return TestClient(app)


class TestAuthRouter:
    """Tests para /auth"""

    def test_register_success(self, client):
        """Test registro exitoso retorna 201."""
        mock_response = {
            "id": str(uuid.uuid4()),
            "email": "test@example.com",
            "first_name": "Juan",
            "last_name": "Pérez",
            "user_type": "traveler",
        }

        with patch("routes.auth_router.Mediator.send", new_callable=AsyncMock, return_value=mock_response):
            with patch("routes.auth_router._link_guest_reservations", new_callable=AsyncMock):
                response = client.post("/auth/register", json={
                    "email": "test@example.com",
                    "password": "SecurePass123!",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "user_type": "traveler",
                })

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["user_type"] == "traveler"

    def test_register_conflict(self, client):
        """Test registro con email duplicado retorna 409."""
        with patch("routes.auth_router.Mediator.send", new_callable=AsyncMock, side_effect=ValueError("Email ya registrado")):
            response = client.post("/auth/register", json={
                "email": "duplicate@example.com",
                "password": "SecurePass123!",
                "first_name": "Juan",
                "last_name": "Pérez",
                "user_type": "traveler",
            })

        assert response.status_code == 409
        assert "ya registrado" in response.json()["detail"]

    def test_login_success(self, client):
        """Test login exitoso retorna token JWT."""
        mock_response = {
            "access_token": "mock_jwt_token",
            "token_type": "bearer",
            "user_type": "traveler",
            "first_name": "Juan",
            "last_name": "Pérez",
            "email": "test@example.com",
        }

        with patch("routes.auth_router.Mediator.send", new_callable=AsyncMock, return_value=mock_response):
            response = client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            })

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "mock_jwt_token"
        assert data["token_type"] == "bearer"
        assert data["first_name"] == "Juan"
        assert data["last_name"] == "Pérez"
        assert data["email"] == "test@example.com"

    def test_login_unauthorized(self, client):
        """Test login con credenciales inválidas retorna 401."""
        with patch("routes.auth_router.Mediator.send", new_callable=AsyncMock, side_effect=ValueError("Credenciales inválidas")):
            response = client.post("/auth/login", json={
                "email": "test@example.com",
                "password": "WrongPass",
            })

        assert response.status_code == 401
        assert "Credenciales" in response.json()["detail"]

    def test_register_invalid_payload(self, client):
        """Test registro con payload inválido retorna 422."""
        response = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "123",
        })
        assert response.status_code == 422
