"""
Tests unitarios para el router de reservaciones.
"""
import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from routes.reservation_router import router as reservation_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(reservation_router)
    return TestClient(app)


class TestReservationRouter:
    """Tests para /reservations"""

    def test_create_reservation_success(self, client):
        """Test crear reservación exitosa."""
        mock_response = {
            "id": "d1000000-0000-0000-0000-000000000001",
            "user_id": None,
            "confirmation_code": "RES123456",
            "status": "pending",
            "message": "Reservación creada exitosamente",
            "hotel": {
                "id": "b1000000-0000-0000-0000-000000000001",
                "name": "Hotel Test",
                "description": None,
                "address": "Calle 123",
                "city": "Bogotá",
                "stars": 4,
                "rating": 4.5,
            },
            "room_type": {
                "id": "c1000000-0000-0000-0000-000000000101",
                "name": "Deluxe",
                "description": None,
                "max_capacity": 2,
                "bed_type": "King",
                "size_sqm": 35.0,
            },
            "pricing": {
                "nights": 4,
                "guests": 2,
                "price_per_night": "131.25",
                "subtotal": "525.00",
                "taxes": "50.00",
                "discounts": "25.00",
                "total": "525.00",
                "currency_code": "USD",
            },
            "check_in": "2026-05-01",
            "check_out": "2026-05-05",
        }

        with patch("routes.reservation_router.Mediator.send_async", return_value=mock_response):
            response = client.post("/reservations", json={
                "hotel_id": "b1000000-0000-0000-0000-000000000001",
                "room_type_id": "c1000000-0000-0000-0000-000000000101",
                "check_in": "2026-05-01",
                "check_out": "2026-05-05",
                "guests": 2,
                "base_price": "500.00",
                "taxes": "50.00",
                "discounts": "25.00",
                "total_price": "525.00",
                "currency_code": "USD",
                "primary_guest": {
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "document_type": "CC",
                    "document_number": "1234567890",
                    "nationality": "COL",
                },
                "payment": {
                    "amount": "525.00",
                    "currency_code": "USD",
                    "payment_token": "tok_visa_4242",
                },
            })

        assert response.status_code == 200
        data = response.json()
        assert data["confirmation_code"].startswith("RES")
        assert data["status"] == "pending"
        assert data["pricing"]["total"] == "525.00"

    def test_create_reservation_bad_request(self, client):
        """Test crear reservación con datos inválidos retorna 400."""
        with patch("routes.reservation_router.Mediator.send_async", side_effect=ValueError("Datos inválidos")):
            response = client.post("/reservations", json={
                "hotel_id": "b1000000-0000-0000-0000-000000000001",
                "room_type_id": "c1000000-0000-0000-0000-000000000101",
                "check_in": "2026-05-01",
                "check_out": "2026-05-05",
                "guests": 2,
                "base_price": "500.00",
                "taxes": "50.00",
                "discounts": "25.00",
                "total_price": "525.00",
                "currency_code": "USD",
                "primary_guest": {
                    "first_name": "Juan",
                    "last_name": "Pérez",
                },
                "payment": {
                    "amount": "525.00",
                    "currency_code": "USD",
                    "payment_token": "tok_123",
                },
            })

        assert response.status_code == 400
        assert "inválidos" in response.json()["detail"]

    def test_get_reservation_by_id_success(self, client):
        """Test obtener reservación por ID exitoso."""
        mock_response = {
            "id": "d1000000-0000-0000-0000-000000000001",
            "user_id": "a2000000-0000-0000-0000-000000000001",
            "hotel_id": "b1000000-0000-0000-0000-000000000001",
            "room_type_id": "c1000000-0000-0000-0000-000000000101",
            "cart_id": None,
            "check_in": "2026-05-01",
            "check_out": "2026-05-05",
            "guests": 2,
            "base_price": "500.00",
            "taxes": "50.00",
            "discounts": "25.00",
            "total_price": "525.00",
            "currency_code": "USD",
            "status": "confirmed",
            "cancellation_policy": None,
            "special_requests": None,
            "confirmation_code": "RES123456",
            "created_at": "2026-01-01T12:00:00",
            "updated_at": None,
        }

        with patch("routes.reservation_router.Mediator.send_async", return_value=mock_response):
            response = client.get("/reservations/d1000000-0000-0000-0000-000000000001")

        assert response.status_code == 200
        data = response.json()
        assert data["confirmation_code"] == "RES123456"
        assert data["status"] == "confirmed"

    def test_get_reservation_by_id_not_found(self, client):
        """Test obtener reservación por ID inexistente retorna 404."""
        with patch("routes.reservation_router.Mediator.send_async", side_effect=ValueError("Reservación no encontrada")):
            response = client.get("/reservations/d1000000-0000-0000-0000-000000000999")

        assert response.status_code == 404
        assert "no encontrada" in response.json()["detail"]

    def test_get_reservation_by_code_success(self, client):
        """Test obtener reservación por código exitoso."""
        mock_response = {
            "id": "d1000000-0000-0000-0000-000000000001",
            "user_id": "a2000000-0000-0000-0000-000000000001",
            "hotel_id": "b1000000-0000-0000-0000-000000000001",
            "room_type_id": "c1000000-0000-0000-0000-000000000101",
            "cart_id": None,
            "check_in": "2026-05-01",
            "check_out": "2026-05-05",
            "guests": 2,
            "base_price": "500.00",
            "taxes": "50.00",
            "discounts": "25.00",
            "total_price": "525.00",
            "currency_code": "USD",
            "status": "confirmed",
            "cancellation_policy": None,
            "special_requests": None,
            "confirmation_code": "RESABC123",
            "created_at": "2026-01-01T12:00:00",
            "updated_at": None,
        }

        with patch("routes.reservation_router.Mediator.send_async", return_value=mock_response):
            response = client.get("/reservations/code/RESABC123")

        assert response.status_code == 200
        data = response.json()
        assert data["confirmation_code"] == "RESABC123"

    def test_list_reservations_by_user_success(self, client):
        """Test listar reservaciones por usuario exitoso."""
        mock_response = {
            "items": [
                {
                    "id": "d1000000-0000-0000-0000-000000000001",
                    "user_id": "a2000000-0000-0000-0000-000000000001",
                    "hotel_id": "b1000000-0000-0000-0000-000000000001",
                    "room_type_id": "c1000000-0000-0000-0000-000000000101",
                    "cart_id": None,
                    "check_in": "2026-05-01",
                    "check_out": "2026-05-05",
                    "guests": 2,
                    "base_price": "500.00",
                    "taxes": "50.00",
                    "discounts": "25.00",
                    "total_price": "525.00",
                    "currency_code": "USD",
                    "status": "confirmed",
                    "cancellation_policy": None,
                    "special_requests": None,
                    "confirmation_code": "RES001",
                    "created_at": "2026-01-01T12:00:00",
                    "updated_at": None,
                }
            ],
            "total": 1,
            "limit": 10,
            "offset": 0,
        }

        with patch("routes.reservation_router.Mediator.send_async", return_value=mock_response):
            response = client.get("/reservations/user/a2000000-0000-0000-0000-000000000001")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1

    def test_list_all_reservations_success(self, client):
        """Test listar todas las reservaciones exitoso."""
        mock_response = {
            "items": [],
            "total": 0,
            "limit": 10,
            "offset": 0,
        }

        with patch("routes.reservation_router.Mediator.send_async", return_value=mock_response):
            response = client.get("/reservations")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_update_reservation_status_success(self, client):
        """Test actualizar estado de reservación exitoso."""
        mock_response = {
            "id": "d1000000-0000-0000-0000-000000000001",
            "previous_status": "pending",
            "new_status": "confirmed",
            "message": "Estado actualizado de 'pending' a 'confirmed'",
        }

        with patch("routes.reservation_router.Mediator.send_async", return_value=mock_response):
            response = client.patch("/reservations/d1000000-0000-0000-0000-000000000001/status", json={
                "status": "confirmed"
            })

        assert response.status_code == 200
        data = response.json()
        assert data["previous_status"] == "pending"
        assert data["new_status"] == "confirmed"

    def test_update_reservation_status_not_found(self, client):
        """Test actualizar estado de reservación inexistente retorna 400."""
        with patch("routes.reservation_router.Mediator.send_async", side_effect=ValueError("Reservación no encontrada")):
            response = client.patch("/reservations/d1000000-0000-0000-0000-000000000999/status", json={
                "status": "confirmed"
            })

        assert response.status_code == 400
        assert "no encontrada" in response.json()["detail"]

    def test_create_reservation_invalid_payload(self, client):
        """Test crear reservación con payload inválido retorna 422."""
        response = client.post("/reservations", json={
            "hotel_id": "not-a-uuid",
        })
        assert response.status_code == 422
