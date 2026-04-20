"""
Tests unitarios para los handlers de consulta de reservaciones.
"""
import uuid
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from reservation_service.queries.reservation_queries import (
    GetReservationByIdQuery,
    GetReservationByCodeQuery,
    ListReservationsByUserQuery,
    ListAllReservationsQuery,
    ReservationResponse,
    ReservationListResponse,
)


class TestGetReservationByIdHandler:
    """Tests para GetReservationByIdHandler."""

    @pytest.fixture
    def mock_reservation(self):
        """Mock de reservación existente."""
        reservation = MagicMock()
        reservation.id = uuid.UUID("d1000000-0000-0000-0000-000000000001")
        reservation.user_id = uuid.UUID("a2000000-0000-0000-0000-000000000001")
        reservation.hotel_id = uuid.UUID("b1000000-0000-0000-0000-000000000001")
        reservation.room_type_id = uuid.UUID("c1000000-0000-0000-0000-000000000101")
        reservation.cart_id = None
        reservation.check_in = date(2026, 5, 1)
        reservation.check_out = date(2026, 5, 5)
        reservation.guests = 2
        reservation.base_price = Decimal("500.00")
        reservation.taxes = Decimal("50.00")
        reservation.discounts = Decimal("25.00")
        reservation.total_price = Decimal("525.00")
        reservation.currency_code = "USD"
        reservation.status = "pending"
        reservation.cancellation_policy = None
        reservation.special_requests = None
        reservation.confirmation_code = "RES123456"
        reservation.created_at = datetime(2026, 1, 1, 12, 0, 0)
        reservation.updated_at = None
        return reservation

    @pytest.mark.asyncio
    async def test_get_reservation_by_id_success(self, mock_reservation):
        """Test consulta por ID exitosa."""
        with patch("reservation_service.queries.get_reservation_handler.async_session_maker") as mock_session_maker, \
             patch("reservation_service.queries.get_reservation_handler.ReservationRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = mock_reservation
            mock_repo_class.return_value = mock_repo

            from reservation_service.queries.get_reservation_handler import GetReservationByIdHandler
            handler = GetReservationByIdHandler()
            query = GetReservationByIdQuery(reservation_id=mock_reservation.id)
            result = await handler.handle(query)

            assert isinstance(result, ReservationResponse)
            assert result.id == mock_reservation.id
            assert result.confirmation_code == "RES123456"
            assert result.status == "pending"
            assert result.total_price == Decimal("525.00")

    @pytest.mark.asyncio
    async def test_get_reservation_by_id_not_found(self):
        """Test consulta por ID falla cuando no existe."""
        with patch("reservation_service.queries.get_reservation_handler.async_session_maker") as mock_session_maker, \
             patch("reservation_service.queries.get_reservation_handler.ReservationRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            from reservation_service.queries.get_reservation_handler import GetReservationByIdHandler
            handler = GetReservationByIdHandler()
            query = GetReservationByIdQuery(reservation_id=uuid.UUID("d1000000-0000-0000-0000-000000000001"))

            with pytest.raises(ValueError, match="no encontrada"):
                await handler.handle(query)


class TestGetReservationByCodeHandler:
    """Tests para GetReservationByCodeHandler."""

    @pytest.fixture
    def mock_reservation(self):
        """Mock de reservación existente."""
        reservation = MagicMock()
        reservation.id = uuid.UUID("d1000000-0000-0000-0000-000000000001")
        reservation.user_id = uuid.UUID("a2000000-0000-0000-0000-000000000001")
        reservation.hotel_id = uuid.UUID("b1000000-0000-0000-0000-000000000001")
        reservation.room_type_id = uuid.UUID("c1000000-0000-0000-0000-000000000101")
        reservation.cart_id = None
        reservation.check_in = date(2026, 5, 1)
        reservation.check_out = date(2026, 5, 5)
        reservation.guests = 2
        reservation.base_price = Decimal("500.00")
        reservation.taxes = Decimal("50.00")
        reservation.discounts = Decimal("25.00")
        reservation.total_price = Decimal("525.00")
        reservation.currency_code = "USD"
        reservation.status = "confirmed"
        reservation.cancellation_policy = None
        reservation.special_requests = None
        reservation.confirmation_code = "RESABC123"
        reservation.created_at = datetime(2026, 1, 1, 12, 0, 0)
        reservation.updated_at = datetime(2026, 1, 2, 10, 0, 0)
        return reservation

    @pytest.mark.asyncio
    async def test_get_reservation_by_code_success(self, mock_reservation):
        """Test consulta por código exitosa."""
        with patch("reservation_service.queries.get_reservation_handler.async_session_maker") as mock_session_maker, \
             patch("reservation_service.queries.get_reservation_handler.ReservationRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_confirmation_code.return_value = mock_reservation
            mock_repo_class.return_value = mock_repo

            from reservation_service.queries.get_reservation_handler import GetReservationByCodeHandler
            handler = GetReservationByCodeHandler()
            query = GetReservationByCodeQuery(confirmation_code="RESABC123")
            result = await handler.handle(query)

            assert isinstance(result, ReservationResponse)
            assert result.confirmation_code == "RESABC123"
            assert result.status == "confirmed"

    @pytest.mark.asyncio
    async def test_get_reservation_by_code_not_found(self):
        """Test consulta por código falla cuando no existe."""
        with patch("reservation_service.queries.get_reservation_handler.async_session_maker") as mock_session_maker, \
             patch("reservation_service.queries.get_reservation_handler.ReservationRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_confirmation_code.return_value = None
            mock_repo_class.return_value = mock_repo

            from reservation_service.queries.get_reservation_handler import GetReservationByCodeHandler
            handler = GetReservationByCodeHandler()
            query = GetReservationByCodeQuery(confirmation_code="RESNONEXISTENT")

            with pytest.raises(ValueError, match="no encontrada"):
                await handler.handle(query)


class TestListReservationsByUserHandler:
    """Tests para ListReservationsByUserHandler."""

    @pytest.fixture
    def mock_reservations(self):
        """Mock de lista de reservaciones."""
        reservations = []
        for i in range(3):
            r = MagicMock()
            r.id = uuid.UUID(f"d1000000-0000-0000-0000-00000000000{i+1}")
            r.user_id = uuid.UUID("a2000000-0000-0000-0000-000000000001")
            r.hotel_id = uuid.UUID("b1000000-0000-0000-0000-000000000001")
            r.room_type_id = uuid.UUID("c1000000-0000-0000-0000-000000000101")
            r.cart_id = None
            r.check_in = date(2026, 5, 1)
            r.check_out = date(2026, 5, 5)
            r.guests = 2
            r.base_price = Decimal("500.00")
            r.taxes = Decimal("50.00")
            r.discounts = Decimal("0.00")
            r.total_price = Decimal("550.00")
            r.currency_code = "USD"
            r.status = "confirmed"
            r.cancellation_policy = None
            r.special_requests = None
            r.confirmation_code = f"RES00{i+1}"
            r.created_at = datetime(2026, 1, i + 1, 12, 0, 0)
            r.updated_at = None
            reservations.append(r)
        return reservations

    @pytest.mark.asyncio
    async def test_list_by_user_success(self, mock_reservations):
        """Test listado por usuario exitoso."""
        with patch("reservation_service.queries.get_reservation_handler.async_session_maker") as mock_session_maker, \
             patch("reservation_service.queries.get_reservation_handler.ReservationRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.list_by_user_or_guest.return_value = mock_reservations
            mock_repo_class.return_value = mock_repo

            from reservation_service.queries.get_reservation_handler import ListReservationsByUserHandler
            handler = ListReservationsByUserHandler()
            query = ListReservationsByUserQuery(
                user_id=uuid.UUID("a2000000-0000-0000-0000-000000000001"),
                limit=10,
                offset=0,
            )
            result = await handler.handle(query)

            assert isinstance(result, ReservationListResponse)
            assert len(result.items) == 3
            assert result.total == 3
            assert result.limit == 10
            assert result.offset == 0
            assert result.items[0].confirmation_code == "RES001"

    @pytest.mark.asyncio
    async def test_list_by_user_empty(self):
        """Test listado por usuario retorna lista vacía."""
        with patch("reservation_service.queries.get_reservation_handler.async_session_maker") as mock_session_maker, \
             patch("reservation_service.queries.get_reservation_handler.ReservationRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.list_by_user_or_guest.return_value = []
            mock_repo_class.return_value = mock_repo

            from reservation_service.queries.get_reservation_handler import ListReservationsByUserHandler
            handler = ListReservationsByUserHandler()
            query = ListReservationsByUserQuery(
                user_id=uuid.UUID("a2000000-0000-0000-0000-000000000001"),
            )
            result = await handler.handle(query)

            assert isinstance(result, ReservationListResponse)
            assert len(result.items) == 0
            assert result.total == 0


class TestListAllReservationsHandler:
    """Tests para ListAllReservationsHandler."""

    @pytest.fixture
    def mock_reservations(self):
        """Mock de lista de reservaciones."""
        reservations = []
        for i in range(5):
            r = MagicMock()
            r.id = uuid.UUID(f"d1000000-0000-0000-0000-00000000000{i+1}")
            r.user_id = uuid.UUID(f"a2000000-0000-0000-0000-00000000000{i+1}")
            r.hotel_id = uuid.UUID("b1000000-0000-0000-0000-000000000001")
            r.room_type_id = uuid.UUID("c1000000-0000-0000-0000-000000000101")
            r.cart_id = None
            r.check_in = date(2026, 6, 1)
            r.check_out = date(2026, 6, 3)
            r.guests = 1
            r.base_price = Decimal("300.00")
            r.taxes = Decimal("30.00")
            r.discounts = Decimal("0.00")
            r.total_price = Decimal("330.00")
            r.currency_code = "USD"
            r.status = "pending"
            r.cancellation_policy = None
            r.special_requests = None
            r.confirmation_code = f"ALL00{i+1}"
            r.created_at = datetime(2026, 2, i + 1, 12, 0, 0)
            r.updated_at = None
            reservations.append(r)
        return reservations

    @pytest.mark.asyncio
    async def test_list_all_success(self, mock_reservations):
        """Test listado de todas las reservaciones exitoso."""
        with patch("reservation_service.queries.get_reservation_handler.async_session_maker") as mock_session_maker, \
             patch("reservation_service.queries.get_reservation_handler.ReservationRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.list_all.return_value = mock_reservations
            mock_repo_class.return_value = mock_repo

            from reservation_service.queries.get_reservation_handler import ListAllReservationsHandler
            handler = ListAllReservationsHandler()
            query = ListAllReservationsQuery(limit=20, offset=0)
            result = await handler.handle(query)

            assert isinstance(result, ReservationListResponse)
            assert len(result.items) == 5
            assert result.total == 5
            assert result.limit == 20
            assert result.offset == 0

    def test_reservation_response_from_orm(self):
        """Test conversión de ORM a ReservationResponse."""
        reservation = MagicMock()
        reservation.id = uuid.UUID("d1000000-0000-0000-0000-000000000001")
        reservation.user_id = uuid.UUID("a2000000-0000-0000-0000-000000000001")
        reservation.hotel_id = uuid.UUID("b1000000-0000-0000-0000-000000000001")
        reservation.room_type_id = uuid.UUID("c1000000-0000-0000-0000-000000000101")
        reservation.cart_id = None
        reservation.check_in = date(2026, 5, 1)
        reservation.check_out = date(2026, 5, 5)
        reservation.guests = 2
        reservation.base_price = Decimal("500.00")
        reservation.taxes = Decimal("50.00")
        reservation.discounts = Decimal("25.00")
        reservation.total_price = Decimal("525.00")
        reservation.currency_code = "USD"
        reservation.status = "pending"
        reservation.cancellation_policy = "flexible"
        reservation.special_requests = "Vista al mar"
        reservation.confirmation_code = "RES123456"
        reservation.created_at = datetime(2026, 1, 1, 12, 0, 0)
        reservation.updated_at = None

        response = ReservationResponse.from_orm(reservation)

        assert response.id == reservation.id
        assert response.confirmation_code == "RES123456"
        assert response.status == "pending"
        assert response.total_price == Decimal("525.00")
        assert response.special_requests == "Vista al mar"
