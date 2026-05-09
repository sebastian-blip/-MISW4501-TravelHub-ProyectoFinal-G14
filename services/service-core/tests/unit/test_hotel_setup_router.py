"""
Tests unitarios para el router de creación completa de hotel (hotel_setup_router).
"""
import uuid
from datetime import time
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.hotel_setup_router import router as hotel_setup_router, get_session


def _build_payload():
    return {
        "hotel": {
            "name": "Hotel Paradise",
            "description": "Un hotel de lujo",
            "address": "Calle 123 # 45-67",
            "city": "Cartagena",
            "country_id": "11111111-1111-1111-1111-111111111111",
            "latitude": 10.3910,
            "longitude": -75.4794,
            "phone": "+57 300 123 4567",
            "email": "reservas@paradise.com",
            "stars": 5,
            "check_in_time": "15:00:00",
            "check_out_time": "11:00:00",
        },
        "owner": {
            "email": "owner@paradise.com",
            "password": "SuperSecret123",
            "first_name": "Juan",
            "last_name": "Pérez",
            "phone": "+57 300 999 8888",
            "country_id": "11111111-1111-1111-1111-111111111111",
        },
        "rooms": [
            {
                "name": "Suite Junior",
                "description": "Habitación con vista al mar",
                "base_price": "200.00",
                "max_capacity": 2,
                "bed_type": "King",
                "size_sqm": "35.0",
                "total_units": 5,
                "amenities": ["wifi", "pool", "breakfast_included"],
            },
            {
                "name": "Doble Estándar",
                "description": "Ideal para familias",
                "base_price": "120.00",
                "max_capacity": 4,
                "bed_type": "Two Queens",
                "size_sqm": "28.0",
                "total_units": 8,
                "amenities": ["parking", "gym", "pet_friendly", "wifi"],
            },
            {
                "name": "Individual",
                "description": "Económica y cómoda",
                "base_price": "80.00",
                "max_capacity": 1,
                "bed_type": "Single",
                "size_sqm": "18.0",
                "total_units": 10,
                "amenities": ["room_service", "wifi", "breakfast_included"],
            },
        ],
    }


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(hotel_setup_router)

    mock_session = MagicMock()
    added_objects = []

    def mock_add(obj):
        added_objects.append(obj)

    async def mock_flush():
        for obj in added_objects:
            if getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()

    mock_session.add = mock_add
    mock_session.flush = AsyncMock(side_effect=mock_flush)
    mock_session.commit = AsyncMock()

    # Por defecto no hay usuario existente
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    return TestClient(app), mock_session


class TestHotelSetupSuccess:
    def test_create_full_hotel_setup_success(self, client):
        test_client, mock_session = client
        payload = _build_payload()

        response = test_client.post("/hotel-setup", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert "hotel_id" in data
        assert "owner_user_id" in data
        assert len(data["rooms"]) == 3
        assert data["rooms"][0]["amenities"] == ["wifi", "pool", "breakfast_included"]
        mock_session.commit.assert_awaited_once()


class TestHotelSetupValidations:
    def test_invalid_room_count_less_than_three(self, client):
        test_client, _ = client
        payload = _build_payload()
        payload["rooms"] = payload["rooms"][:2]

        response = test_client.post("/hotel-setup", json=payload)
        assert response.status_code == 422
        assert "exactamente 3" in response.text.lower() or "rooms" in response.text.lower()

    def test_invalid_room_count_more_than_three(self, client):
        test_client, _ = client
        payload = _build_payload()
        payload["rooms"].append(payload["rooms"][0])

        response = test_client.post("/hotel-setup", json=payload)
        assert response.status_code == 422

    def test_room_with_less_than_three_amenities(self, client):
        test_client, _ = client
        payload = _build_payload()
        payload["rooms"][0]["amenities"] = ["wifi"]

        response = test_client.post("/hotel-setup", json=payload)
        assert response.status_code == 422
        assert "al menos 3" in response.text.lower()

    def test_room_with_invalid_amenity(self, client):
        test_client, _ = client
        payload = _build_payload()
        payload["rooms"][0]["amenities"] = ["wifi", "pool", "jacuzzi"]

        response = test_client.post("/hotel-setup", json=payload)
        assert response.status_code == 422
        assert "inválidas" in response.text.lower()

    def test_duplicate_owner_email(self, client):
        test_client, mock_session = client
        payload = _build_payload()

        # Simular usuario existente
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        response = test_client.post("/hotel-setup", json=payload)
        assert response.status_code == 400
        assert "ya está registrado" in response.json()["detail"]
