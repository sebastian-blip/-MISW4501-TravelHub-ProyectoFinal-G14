"""
Tests unitarios para los handlers de listado de hoteles.
"""
import uuid
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from accommodation_service.queries.accommodation_queries import (
    ListHotelsQuery,
    GetHotelAvailabilityQuery,
    ListCitiesQuery,
    HotelSummary,
    HotelAvailabilityResult,
    RoomTypeAvailability,
    CityInfo,
)


class TestListHotelsHandler:
    """Tests para ListHotelsHandler."""

    @pytest.fixture
    def mock_hotels(self):
        """Mock de lista de hoteles."""
        return [
            HotelSummary(
                id=uuid.UUID("b1000000-0000-0000-0000-000000000001"),
                name="Hotel Test 1",
                description="Descripción 1",
                address="Calle 1",
                city="Bogotá",
                stars=4,
                rating=Decimal("4.5"),
                total_reviews=120,
                active=True,
            ),
            HotelSummary(
                id=uuid.UUID("b1000000-0000-0000-0000-000000000002"),
                name="Hotel Test 2",
                description="Descripción 2",
                address="Calle 2",
                city="Bogotá",
                stars=5,
                rating=Decimal("4.8"),
                total_reviews=300,
                active=True,
            ),
        ]

    @pytest.mark.asyncio
    async def test_list_hotels_success(self, mock_hotels):
        """Test listado de hoteles exitoso."""
        with patch("accommodation_service.queries.hotel_listing_handler.async_session_maker") as mock_session_maker, \
             patch("accommodation_service.queries.hotel_listing_handler.HotelListingRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.list_hotels.return_value = mock_hotels
            mock_repo_class.return_value = mock_repo

            from accommodation_service.queries.hotel_listing_handler import ListHotelsHandler
            handler = ListHotelsHandler()
            query = ListHotelsQuery(city="Bogotá", limit=50, offset=0)
            result = await handler.handle(query)

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0].name == "Hotel Test 1"
            assert result[1].stars == 5
            assert result[0].active is True

    @pytest.mark.asyncio
    async def test_list_hotels_empty(self):
        """Test listado retorna lista vacía."""
        with patch("accommodation_service.queries.hotel_listing_handler.async_session_maker") as mock_session_maker, \
             patch("accommodation_service.queries.hotel_listing_handler.HotelListingRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.list_hotels.return_value = []
            mock_repo_class.return_value = mock_repo

            from accommodation_service.queries.hotel_listing_handler import ListHotelsHandler
            handler = ListHotelsHandler()
            query = ListHotelsQuery(city="CiudadInexistente")
            result = await handler.handle(query)

            assert isinstance(result, list)
            assert len(result) == 0


class TestGetHotelAvailabilityHandler:
    """Tests para GetHotelAvailabilityHandler."""

    @pytest.fixture
    def mock_availability(self):
        """Mock de disponibilidad de hotel."""
        return HotelAvailabilityResult(
            hotel_id=uuid.UUID("b1000000-0000-0000-0000-000000000001"),
            hotel_name="Hotel Test",
            description="Un hotel",
            city="Bogotá",
            stars=4,
            rating=Decimal("4.5"),
            check_in_time="15:00:00",
            check_out_time="11:00:00",
            nights=4,
            available_room_types=[
                RoomTypeAvailability(
                    id=uuid.UUID("c1000000-0000-0000-0000-000000000101"),
                    name="Deluxe",
                    description="Habitación deluxe",
                    max_capacity=2,
                    bed_type="King",
                    size_sqm=Decimal("35.0"),
                    price_per_night=Decimal("131.25"),
                    total_price=Decimal("525.00"),
                    currency_code="USD",
                    minimum_stay=1,
                    amenities=[],
                )
            ],
        )

    @pytest.mark.asyncio
    async def test_get_availability_success(self, mock_availability):
        """Test consulta de disponibilidad exitosa."""
        with patch("accommodation_service.queries.hotel_listing_handler.async_session_maker") as mock_session_maker, \
             patch("accommodation_service.queries.hotel_listing_handler.HotelListingRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_hotel_availability.return_value = mock_availability
            mock_repo_class.return_value = mock_repo

            from accommodation_service.queries.hotel_listing_handler import GetHotelAvailabilityHandler
            handler = GetHotelAvailabilityHandler()
            query = GetHotelAvailabilityQuery(
                hotel_id=uuid.UUID("b1000000-0000-0000-0000-000000000001"),
                check_in=date(2026, 5, 1),
                check_out=date(2026, 5, 5),
                guests=2,
            )
            result = await handler.handle(query)

            assert isinstance(result, HotelAvailabilityResult)
            assert result.hotel_name == "Hotel Test"
            assert result.nights == 4
            assert len(result.available_room_types) == 1
            assert result.available_room_types[0].price_per_night == Decimal("131.25")

    @pytest.mark.asyncio
    async def test_get_availability_not_found(self):
        """Test falla cuando el hotel no existe o no tiene disponibilidad."""
        with patch("accommodation_service.queries.hotel_listing_handler.async_session_maker") as mock_session_maker, \
             patch("accommodation_service.queries.hotel_listing_handler.HotelListingRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_hotel_availability.return_value = None
            mock_repo_class.return_value = mock_repo

            from accommodation_service.queries.hotel_listing_handler import GetHotelAvailabilityHandler
            handler = GetHotelAvailabilityHandler()
            query = GetHotelAvailabilityQuery(
                hotel_id=uuid.UUID("b1000000-0000-0000-0000-000000000999"),
                check_in=date(2026, 5, 1),
                check_out=date(2026, 5, 5),
                guests=2,
            )
            with pytest.raises(ValueError, match="no encontrado"):
                await handler.handle(query)

    @pytest.mark.asyncio
    async def test_get_availability_invalid_dates(self):
        """Test falla con fechas inválidas."""
        from accommodation_service.queries.hotel_listing_handler import GetHotelAvailabilityHandler
        handler = GetHotelAvailabilityHandler()
        query = GetHotelAvailabilityQuery(
            hotel_id=uuid.UUID("b1000000-0000-0000-0000-000000000001"),
            check_in=date(2026, 5, 10),
            check_out=date(2026, 5, 5),
            guests=2,
        )
        with pytest.raises(ValueError, match="check_out debe ser posterior"):
            await handler.handle(query)

    @pytest.mark.asyncio
    async def test_get_availability_invalid_guests(self):
        """Test falla con huéspedes inválidos."""
        from accommodation_service.queries.hotel_listing_handler import GetHotelAvailabilityHandler
        handler = GetHotelAvailabilityHandler()
        query = GetHotelAvailabilityQuery(
            hotel_id=uuid.UUID("b1000000-0000-0000-0000-000000000001"),
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
            guests=0,
        )
        with pytest.raises(ValueError, match="huéspedes"):
            await handler.handle(query)


class TestListCitiesHandler:
    """Tests para ListCitiesHandler."""

    @pytest.fixture
    def mock_cities(self):
        """Mock de lista de ciudades."""
        return [
            CityInfo(
                city="Bogotá",
                country_id=uuid.UUID("a1000000-0000-0000-0000-000000000001"),
                hotel_count=15,
            ),
            CityInfo(
                city="Medellín",
                country_id=uuid.UUID("a1000000-0000-0000-0000-000000000001"),
                hotel_count=8,
            ),
        ]

    @pytest.mark.asyncio
    async def test_list_cities_success(self, mock_cities):
        """Test listado de ciudades exitoso."""
        with patch("accommodation_service.queries.hotel_listing_handler.async_session_maker") as mock_session_maker, \
             patch("accommodation_service.queries.hotel_listing_handler.HotelListingRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.list_cities.return_value = mock_cities
            mock_repo_class.return_value = mock_repo

            from accommodation_service.queries.hotel_listing_handler import ListCitiesHandler
            handler = ListCitiesHandler()
            query = ListCitiesQuery()
            result = await handler.handle(query)

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0].city == "Bogotá"
            assert result[0].hotel_count == 15
            assert result[1].city == "Medellín"

    @pytest.mark.asyncio
    async def test_list_cities_by_country(self, mock_cities):
        """Test listado filtrado por país."""
        with patch("accommodation_service.queries.hotel_listing_handler.async_session_maker") as mock_session_maker, \
             patch("accommodation_service.queries.hotel_listing_handler.HotelListingRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.list_cities.return_value = mock_cities[:1]
            mock_repo_class.return_value = mock_repo

            from accommodation_service.queries.hotel_listing_handler import ListCitiesHandler
            handler = ListCitiesHandler()
            query = ListCitiesQuery(country_id=uuid.UUID("a1000000-0000-0000-0000-000000000001"))
            result = await handler.handle(query)

            assert len(result) == 1
            assert result[0].city == "Bogotá"

    def test_hotel_summary_structure(self):
        """Test estructura de HotelSummary."""
        summary = HotelSummary(
            id=uuid.UUID("b1000000-0000-0000-0000-000000000001"),
            name="Hotel Test",
            description="Descripción",
            address="Calle 123",
            city="Bogotá",
            stars=4,
            rating=Decimal("4.5"),
            total_reviews=100,
            active=True,
        )
        assert summary.stars == 4
        assert summary.rating == Decimal("4.5")
        assert summary.active is True

    def test_city_info_structure(self):
        """Test estructura de CityInfo."""
        city = CityInfo(
            city="Cartagena",
            country_id=uuid.UUID("a1000000-0000-0000-0000-000000000001"),
            hotel_count=5,
        )
        assert city.city == "Cartagena"
        assert city.hotel_count == 5
