"""
Tests unitarios para el router de flujo de reservaciones (state machine).
"""
import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from routes.reservation_state_machine_router import router as flow_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(flow_router)
    return TestClient(app)


class TestReservationFlowRouter:
    """Tests para /reservation-flow"""

    def test_create_flow_success(self, client):
        """Test flujo de creación exitoso."""
        mock_result = {
            "completed": True,
            "step": "create",
            "history": ["validate", "create"],
            "result": {
                "success": True,
                "proceed": True,
                "confirmation_code": "RES999999",
                "reservation_id": "d1000000-0000-0000-0000-000000000001",
                "status": "pending",
                "message": "Reservación creada",
                "hotel": {"name": "Hotel Test"},
                "room_type": {"name": "Deluxe"},
                "pricing": {"total": "525.00"},
            }
        }

        with patch("routes.reservation_state_machine_router.SimpleReservationFlow.run_create_flow", return_value=mock_result):
            response = client.post("/reservation-flow/create", json={
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
            }, headers={"X-Guest-Id": "a1000000-0000-0000-0000-000000000001"})

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True
        assert data["result"]["confirmation_code"] == "RES999999"

    def test_create_flow_completed_false_returns_400(self, client):
        """Test flujo de creación con completed=False retorna 400."""
        mock_result = {
            "completed": False,
            "step": "create",
            "result": {
                "success": False,
                "proceed": False,
                "error": "No hay disponibilidad para la fecha 2026-05-03",
                "message": "Error al crear: No hay disponibilidad para la fecha 2026-05-03"
            }
        }

        with patch("routes.reservation_state_machine_router.SimpleReservationFlow.run_create_flow", return_value=mock_result):
            response = client.post("/reservation-flow/create", json={
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
            }, headers={"X-Guest-Id": "a1000000-0000-0000-0000-000000000001"})

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["completed"] is False
        assert "No hay disponibilidad" in data["detail"]["result"]["message"]

    def test_create_flow_validation_error(self, client):
        """Test flujo de creación con error interno retorna 500."""
        with patch("routes.reservation_state_machine_router.SimpleReservationFlow.run_create_flow", side_effect=Exception("DB Error")):
            response = client.post("/reservation-flow/create", json={
                "hotel_id": "b1000000-0000-0000-0000-000000000001",
                "room_type_id": "c1000000-0000-0000-0000-000000000101",
                "check_in": "2026-05-01",
                "check_out": "2026-05-05",
                "guests": 2,
                "primary_guest": {
                    "first_name": "Juan",
                    "last_name": "Pérez",
                },
                "payment": {
                    "amount": "525.00",
                    "currency_code": "USD",
                    "payment_token": "tok_123",
                },
            }, headers={"X-Guest-Id": "a1000000-0000-0000-0000-000000000001"})

        assert response.status_code == 500
        assert "DB Error" in response.json()["detail"]

    def test_check_reservation_success(self, client):
        """Test consulta de reserva por código exitosa."""
        mock_response = MagicMock()
        mock_response.id = uuid.UUID("d1000000-0000-0000-0000-000000000001")
        mock_response.confirmation_code = "RESABC123"
        mock_response.status = "confirmed"
        mock_response.total_price = 525.00

        with patch("mediatr.Mediator.send_async", new_callable=AsyncMock, return_value=mock_response):
            response = client.get("/reservation-flow/check/RESABC123")

        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["reservation"]["confirmation_code"] == "RESABC123"

    def test_check_reservation_not_found(self, client):
        """Test consulta de reserva por código inexistente."""
        with patch("mediatr.Mediator.send_async", new_callable=AsyncMock, side_effect=ValueError("Reserva no encontrada")):
            response = client.get("/reservation-flow/check/RESNONEXISTENT")

        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False
        assert "no encontrada" in data["message"]

    def test_payment_flow_completed_false_returns_400(self, client):
        """Test flujo de pago con completed=False retorna 400."""
        mock_result = {
            "completed": False,
            "step": "validate_time",
            "result": {
                "success": False,
                "proceed": False,
                "error": "La reserva ya está confirmada",
                "confirmation_code": "RES123"
            }
        }

        with patch("routes.reservation_state_machine_router.SimpleReservationFlow.run_payment_flow", return_value=mock_result):
            response = client.post("/reservation-flow/payment", json={
                "reservation_id": "d1000000-0000-0000-0000-000000000001",
                "primary_guest": {
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "email": "juan@example.com"
                },
                "payment": {
                    "amount": "525.00",
                    "currency_code": "USD",
                    "payment_token": "tok_visa_4242"
                }
            }, headers={"X-Guest-Id": "a1000000-0000-0000-0000-000000000001"})

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["completed"] is False
        assert "ya está confirmada" in data["detail"]["result"]["error"]

    def test_create_flow_invalid_payload(self, client):
        """Test flujo de creación con payload inválido retorna 422."""
        response = client.post("/reservation-flow/create", json={
            "hotel_id": "not-a-uuid",
        })
        assert response.status_code == 422
