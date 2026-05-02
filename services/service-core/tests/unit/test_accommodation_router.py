"""
Tests unitarios para el router de alojamientos.
"""
import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from routes.accommodation_router import router as accommodation_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(accommodation_router)
    return TestClient(app)


class TestAccommodationRouter:
    """Tests para /accommodations"""

    def test_search_accommodations_success(self, client):
        """Test búsqueda de alojamientos exitosa."""
        # Crear mocks con atributos que el router espera
        room_type = MagicMock()
        room_type.id = uuid.UUID("c1000000-0000-0000-0000-000000000101")
        room_type.name = "Deluxe"
        room_type.description = "Habitación espaciosa"
        room_type.max_capacity = 2
        room_type.bed_type = "King"
        room_type.size_sqm = 35.0
        room_type.price_per_night = 131.25
        room_type.total_price = 525.00
        room_type.currency_code = "USD"
        room_type.minimum_stay = 1
        amenity = MagicMock()
        amenity.name = "WiFi"
        amenity.icon = "wifi"
        room_type.amenities = [amenity]

        result = MagicMock()
        result.hotel_id = uuid.UUID("b1000000-0000-0000-0000-000000000001")
        result.hotel_name = "Hotel Test"
        result.description = "Un hotel de prueba"
        result.address = "Calle 123"
        result.city = "Bogotá"
        result.stars = 4
        result.rating = 4.5
        result.check_in_time = "15:00:00"
        result.check_out_time = "11:00:00"
        result.available_room_types = [room_type]

        mock_page = MagicMock()
        mock_page.page = 2
        mock_page.page_size = 10
        mock_page.items = [result]

        with patch("routes.accommodation_router.Mediator.send", new_callable=AsyncMock, return_value=mock_page):
            response = client.get("/accommodations/search?city=Bogotá&check_in=2026-05-01&check_out=2026-05-05&guests=2", headers={"X-Guest-Id": "guest-123"})

        assert response.status_code == 200
        data = response.json()
        assert "user_session" in data
        assert "result" in data
        assert len(data["result"]) == 1
        assert data["result"][0]["hotel_name"] == "Hotel Test"
        assert data["result"][0]["city"] == "Bogotá"
        assert len(data["result"][0]["available_room_types"]) == 1

    def test_search_accommodations_bad_request(self, client):
        """Test búsqueda con fechas inválidas retorna 400."""
        with patch("routes.accommodation_router.Mediator.send", new_callable=AsyncMock, side_effect=ValueError("check_out debe ser posterior")):
            response = client.get("/accommodations/search?city=Bogotá&check_in=2026-05-10&check_out=2026-05-05&guests=2", headers={"X-Guest-Id": "guest-123"})

        assert response.status_code == 400
        assert "check_out" in response.json()["detail"]

    def test_search_accommodations_missing_params(self, client):
        """Test búsqueda sin parámetros requeridos retorna 422."""
        response = client.get("/accommodations/search")
        assert response.status_code == 422

    def test_list_hotels_success(self, client):
        """Test listado de hoteles exitoso."""
        hotel1 = MagicMock()
        hotel1.id = uuid.UUID("b1000000-0000-0000-0000-000000000001")
        hotel1.name = "Hotel Test 1"
        hotel1.description = "Desc 1"
        hotel1.address = "Calle 1"
        hotel1.city = "Bogotá"
        hotel1.stars = 4
        hotel1.rating = 4.5
        hotel1.total_reviews = 100
        hotel1.active = True

        hotel2 = MagicMock()
        hotel2.id = uuid.UUID("b1000000-0000-0000-0000-000000000002")
        hotel2.name = "Hotel Test 2"
        hotel2.description = "Desc 2"
        hotel2.address = "Calle 2"
        hotel2.city = "Medellín"
        hotel2.stars = 5
        hotel2.rating = 4.8
        hotel2.total_reviews = 200
        hotel2.active = True

        result = [hotel1, hotel2]

        with patch("routes.accommodation_router.Mediator.send", new_callable=AsyncMock, return_value=result):
            response = client.get("/accommodations/hotels")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Hotel Test 1"

    def test_list_hotels_with_filters(self, client):
        """Test listado de hoteles con filtros."""
        hotel = MagicMock()
        hotel.id = uuid.UUID("b1000000-0000-0000-0000-000000000001")
        hotel.name = "Hotel Filtrado"
        hotel.description = None
        hotel.address = "Calle 1"
        hotel.city = "Bogotá"
        hotel.stars = 5
        hotel.rating = 4.9
        hotel.total_reviews = 50
        hotel.active = True

        mock_results = [hotel]

        with patch("routes.accommodation_router.Mediator.send", new_callable=AsyncMock, return_value=mock_results):
            response = client.get("/accommodations/hotels?city=Bogotá&min_stars=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["stars"] == 5

    def test_get_hotel_availability_success(self, client):
        """Test disponibilidad por hotel exitosa."""
        room_type = MagicMock()
        room_type.id = uuid.UUID("c1000000-0000-0000-0000-000000000101")
        room_type.name = "Deluxe"
        room_type.description = None
        room_type.max_capacity = 2
        room_type.bed_type = "King"
        room_type.size_sqm = 35.0
        room_type.price_per_night = 131.25
        room_type.total_price = 525.00
        room_type.currency_code = "USD"
        room_type.minimum_stay = 1
        room_type.amenities = []

        result = MagicMock()
        result.hotel_id = uuid.UUID("b1000000-0000-0000-0000-000000000001")
        result.hotel_name = "Hotel Test"
        result.description = "Un hotel"
        result.city = "Bogotá"
        result.stars = 4
        result.rating = 4.5
        result.check_in_time = "15:00:00"
        result.check_out_time = "11:00:00"
        result.nights = 4
        result.available_room_types = [room_type]

        with patch("routes.accommodation_router.Mediator.send", new_callable=AsyncMock, return_value=result):
            response = client.get("/accommodations/hotels/b1000000-0000-0000-0000-000000000001/availability?check_in=2026-05-01&check_out=2026-05-05&guests=2")

        assert response.status_code == 200
        data = response.json()
        assert data["hotel_name"] == "Hotel Test"
        assert data["nights"] == 4
        assert len(data["available_room_types"]) == 1

    def test_get_hotel_availability_not_found(self, client):
        """Test disponibilidad por hotel inexistente retorna 400."""
        with patch("routes.accommodation_router.Mediator.send", new_callable=AsyncMock, side_effect=ValueError("Hotel no encontrado")):
            response = client.get("/accommodations/hotels/b1000000-0000-0000-0000-000000000999/availability?check_in=2026-05-01&check_out=2026-05-05&guests=2")

        assert response.status_code == 400
        assert "no encontrado" in response.json()["detail"]

    def test_list_cities_success(self, client):
        """Test listado de ciudades exitoso."""
        city1 = MagicMock()
        city1.city = "Bogotá"
        city1.country_id = uuid.UUID("a1000000-0000-0000-0000-000000000001")
        city1.hotel_count = 15

        city2 = MagicMock()
        city2.city = "Medellín"
        city2.country_id = uuid.UUID("a1000000-0000-0000-0000-000000000001")
        city2.hotel_count = 8

        mock_results = [city1, city2]

        with patch("routes.accommodation_router.Mediator.send", new_callable=AsyncMock, return_value=mock_results):
            response = client.get("/accommodations/cities")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["city"] == "Bogotá"
        assert data[0]["hotel_count"] == 15

    def test_list_cities_by_country(self, client):
        """Test listado de ciudades filtrado por país."""
        city1 = MagicMock()
        city1.city = "Bogotá"
        city1.country_id = uuid.UUID("a1000000-0000-0000-0000-000000000001")
        city1.hotel_count = 15

        mock_results = [city1]

        with patch("routes.accommodation_router.Mediator.send", new_callable=AsyncMock, return_value=mock_results):
            response = client.get("/accommodations/cities?country_id=a1000000-0000-0000-0000-000000000001")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
