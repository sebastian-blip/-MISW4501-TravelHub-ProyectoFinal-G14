"""
Tests unitarios para el handler de búsqueda de alojamientos.
"""
import uuid
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from accommodation_service.queries.accommodation_queries import (
    SearchAccommodationsQuery,
    AccommodationSearchResult,
    RoomTypeAvailability,
    RoomAmenityInfo,
)


class TestSearchAccommodationsHandler:
    """Tests para SearchAccommodationsHandler."""

    @pytest.fixture
    def valid_query(self):
        """Query base válida."""
        return SearchAccommodationsQuery(
            city="Bogotá",
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
            guests=2,
        )

    @pytest.fixture
    def mock_results(self):
        """Mock de resultados de búsqueda."""
        return [
            AccommodationSearchResult(
                hotel_id=uuid.UUID("b1000000-0000-0000-0000-000000000001"),
                hotel_name="Hotel Test",
                description="Un hotel de prueba",
                address="Calle 123",
                city="Bogotá",
                stars=4,
                rating=Decimal("4.5"),
                check_in_time="15:00:00",
                check_out_time="11:00:00",
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
                        amenities=[
                            RoomAmenityInfo(name="WiFi", icon="wifi"),
                            RoomAmenityInfo(name="Desayuno", icon="breakfast"),
                        ],
                    )
                ],
            )
        ]

    @pytest.mark.asyncio
    async def test_search_success(self, valid_query, mock_results):
        """Test búsqueda exitosa."""
        with patch("accommodation_service.queries.search_accommodations_handler.async_session_maker") as mock_session_maker, \
             patch("accommodation_service.queries.search_accommodations_handler.AccommodationRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.search.return_value = mock_results
            mock_repo_class.return_value = mock_repo

            from accommodation_service.queries.search_accommodations_handler import SearchAccommodationsHandler
            handler = SearchAccommodationsHandler()
            result = await handler.handle(valid_query)

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0].hotel_name == "Hotel Test"
            assert result[0].city == "Bogotá"
            assert len(result[0].available_room_types) == 1
            assert result[0].available_room_types[0].name == "Deluxe"
            assert result[0].available_room_types[0].price_per_night == Decimal("131.25")

    @pytest.mark.asyncio
    async def test_search_invalid_dates(self, valid_query):
        """Test búsqueda falla con fechas inválidas."""
        invalid_query = SearchAccommodationsQuery(
            city="Bogotá",
            check_in=date(2026, 5, 10),
            check_out=date(2026, 5, 5),  # check_out antes que check_in
            guests=2,
        )

        from accommodation_service.queries.search_accommodations_handler import SearchAccommodationsHandler
        handler = SearchAccommodationsHandler()
        with pytest.raises(ValueError, match="check_out debe ser posterior"):
            await handler.handle(invalid_query)

    @pytest.mark.asyncio
    async def test_search_invalid_guests(self, valid_query):
        """Test búsqueda falla con huéspedes inválidos."""
        invalid_query = SearchAccommodationsQuery(
            city="Bogotá",
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
            guests=0,
        )

        from accommodation_service.queries.search_accommodations_handler import SearchAccommodationsHandler
        handler = SearchAccommodationsHandler()
        with pytest.raises(ValueError, match="huspedes"):
            await handler.handle(invalid_query)

    def test_search_query_structure(self, valid_query):
        """Test estructura de la query de búsqueda."""
        assert valid_query.city == "Bogotá"
        assert valid_query.check_in == date(2026, 5, 1)
        assert valid_query.check_out == date(2026, 5, 5)
        assert valid_query.guests == 2

    def test_accommodation_search_result_structure(self, mock_results):
        """Test estructura del resultado de búsqueda."""
        result = mock_results[0]
        assert result.stars == 4
        assert result.rating == Decimal("4.5")
        assert result.available_room_types[0].amenities[0].name == "WiFi"
