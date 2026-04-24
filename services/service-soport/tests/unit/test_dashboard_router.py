import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app  # Asegúrate de que tu app se importa aquí correctamente

client = TestClient(app)

def build_url(start="2026-01-01", end="2026-12-30"):
    return f"/analitycs/dahsboard?start_date={start}&end_date={end}"

def make_headers(token):
    return {"Authorization": f"Bearer {token}"}

FAKE_RESERVATIONS = [
    {
        "id": "a9fe3f49-a6c7-43f6-8e91-3e25a4e8915a",
        "hotel_id": "b1000000-0000-0000-0000-000000000001",
        "room_type_id": "c1000000-0000-0000-0000-000000000101",
        "status": "confirmed",
        "room_type": {
            "id": "c1000000-0000-0000-0000-000000000101",
            "name": "Habitación Estándar",
        }
    },
    {
        "id": "3a65a550-bbd7-426c-be9a-0023977988d7",
        "hotel_id": "b1000000-0000-0000-0000-000000000001",
        "room_type_id": "c1000000-0000-0000-0000-000000000101",
        "status": "cancelled",
        "room_type": {
            "id": "c1000000-0000-0000-0000-000000000101",
            "name": "Habitación Estándar",
        }
    }
]

STAT_RESPONSE = {
    "total_reservas": 2,
    "total_personas": 2,
    "total_ganancias": 525,
    "percent_status": {
        "confirmed": "50.0%",
        "cancelled": "50.0%"
    },
    "revenue_per_day": [
        {
            "date": "2026-05-05",
            "revenue": 525
        }
    ]
}

@pytest.fixture
def mock_token():
    return "testtoken"

@patch("routers.analitycs_router.bookings_stats")  # ← Patch correcto según tu archivo
@patch("requests.get")
def test_dashboard_success(mock_get, mock_bookings_stats, mock_token):
    # Mock respuesta exitosa del servicio core
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": FAKE_RESERVATIONS}
    mock_get.return_value = mock_response

    # bookings_stats produce el dict de estadísticas
    mock_bookings_stats.return_value = STAT_RESPONSE

    # Haz la petición al endpoint
    response = client.get(build_url(), headers=make_headers(mock_token))
    assert response.status_code == 200

    data = response.json()
    # Checa los campos de estadísticas
    assert data["total_reservas"] == 2
    assert data["total_personas"] == 2
    assert data["total_ganancias"] == 525
    assert data["percent_status"] == {"confirmed": "50.0%", "cancelled": "50.0%"}
    assert isinstance(data["revenue_per_day"], list)

    # Checa "reservations"
    assert "reservations" in data
    assert isinstance(data["reservations"], list)
    assert len(data["reservations"]) == 2
    assert data["reservations"][0]["status"] in ("confirmed", "cancelled")

@patch("requests.get")
def test_dashboard_core_service_error(mock_get, mock_token):
    # Respuesta de error del core
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"error": "Internal Error"}
    mock_get.return_value = mock_response

    response = client.get(build_url(), headers=make_headers(mock_token))
    assert response.status_code == 500
    assert "error" in response.json()

@patch("requests.get")
def test_dashboard_exception(mock_get, mock_token):
    # Simular excepción de requests
    mock_get.side_effect = Exception("Connection error")
    response = client.get(build_url(), headers=make_headers(mock_token))
    assert response.status_code == 500
    assert response.text == '"Internal Server Error"'