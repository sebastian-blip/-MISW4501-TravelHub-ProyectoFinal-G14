"""
Tests unitarios para el handler de actualización de estado de reservaciones.
"""
import uuid
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from reservation_service.commands.reservation_commands import (
    UpdateReservationStatusCommand,
    UpdateReservationStatusResponse,
)


class TestUpdateStatusHandler:
    """Tests para handle_update_status."""

    @pytest.fixture
    def reservation_id(self):
        return uuid.UUID("d1000000-0000-0000-0000-000000000001")

    @pytest.fixture
    def mock_reservation(self, reservation_id):
        """Mock de reservación existente."""
        reservation = MagicMock()
        reservation.id = reservation_id
        reservation.user_id = uuid.UUID("a2000000-0000-0000-0000-000000000001")
        reservation.hotel_id = uuid.UUID("b1000000-0000-0000-0000-000000000001")
        reservation.room_type_id = uuid.UUID("c1000000-0000-0000-0000-000000000101")
        reservation.check_in = date(2026, 5, 1)
        reservation.check_out = date(2026, 5, 5)
        reservation.status = "pending"
        reservation.total_price = Decimal("525.00")
        return reservation

    @pytest.mark.asyncio
    async def test_update_status_success(self, reservation_id, mock_reservation):
        """Test actualización de estado exitosa."""
        with patch("reservation_service.commands.update_status_handler.async_session_maker") as mock_session_maker, \
             patch("reservation_service.commands.update_status_handler.ReservationRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = mock_reservation
            mock_repo.update_status.return_value = mock_reservation
            mock_repo_class.return_value = mock_repo

            from reservation_service.commands.update_status_handler import handle_update_status
            command = UpdateReservationStatusCommand(
                reservation_id=reservation_id,
                status="confirmed",
            )
            result = await handle_update_status(command)

            assert isinstance(result, UpdateReservationStatusResponse)
            assert result.id == reservation_id
            assert result.previous_status == "pending"
            assert result.new_status == "confirmed"
            assert "confirmada" in result.message.lower() or "actualizado" in result.message.lower()

    @pytest.mark.asyncio
    async def test_update_status_cancel_restores_inventory(self, reservation_id, mock_reservation):
        """Test que al cancelar se restaura el inventario."""
        mock_inventory = MagicMock()
        mock_inventory.available_units = 0

        # Side effect para session.execute: primera llamada (repo interno) puede
        # retornar cualquier cosa, segunda (inventario) retorna el mock_inventory
        mock_result_inventory = MagicMock()
        mock_result_inventory.scalar_one_or_none.return_value = mock_inventory

        with patch("reservation_service.commands.update_status_handler.async_session_maker") as mock_session_maker, \
             patch("reservation_service.commands.update_status_handler.ReservationRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = mock_reservation
            mock_repo.update_status.return_value = mock_reservation
            mock_repo_class.return_value = mock_repo

            # Configurar execute para retornar el inventario mockeado
            mock_session.execute.return_value = mock_result_inventory

            from reservation_service.commands.update_status_handler import handle_update_status
            command = UpdateReservationStatusCommand(
                reservation_id=reservation_id,
                status="cancelled",
            )
            result = await handle_update_status(command)

            assert result.new_status == "cancelled"
            assert result.previous_status == "pending"
            # Verificar que el inventario fue restaurado (+1 por cada noche)
            # El mock_reservation tiene 4 noches (1-5 Mayo), así que se incrementa 4 veces
            assert mock_inventory.available_units == 4

    @pytest.mark.asyncio
    async def test_update_status_reservation_not_found(self, reservation_id):
        """Test falla cuando la reservación no existe."""
        with patch("reservation_service.commands.update_status_handler.async_session_maker") as mock_session_maker, \
             patch("reservation_service.commands.update_status_handler.ReservationRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            from reservation_service.commands.update_status_handler import handle_update_status
            command = UpdateReservationStatusCommand(
                reservation_id=reservation_id,
                status="confirmed",
            )
            with pytest.raises(ValueError, match="no encontrada"):
                await handle_update_status(command)

    def test_update_status_command_structure(self, reservation_id):
        """Test estructura del comando de actualización."""
        command = UpdateReservationStatusCommand(
            reservation_id=reservation_id,
            status="completed",
        )
        assert command.reservation_id == reservation_id
        assert command.status == "completed"

    def test_update_status_response_structure(self, reservation_id):
        """Test estructura de la respuesta."""
        response = UpdateReservationStatusResponse(
            id=reservation_id,
            previous_status="pending",
            new_status="confirmed",
            message="Estado actualizado de 'pending' a 'confirmed'",
        )
        assert response.previous_status == "pending"
        assert response.new_status == "confirmed"
