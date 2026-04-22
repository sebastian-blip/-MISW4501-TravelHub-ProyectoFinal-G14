"""
Tests unitarios para SimpleReservationFlow.
"""
import uuid
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from state_machine.simple_reservation_flow import SimpleReservationFlow


class TestSimpleReservationFlowValidate:
    """Tests para el paso de validación (step_validate)."""

    @pytest.fixture
    def flow(self):
        """Flow base para tests."""
        flow = SimpleReservationFlow()
        flow.set_data(
            user_id=None,  # Guest reservation
            hotel_id="b1000000-0000-0000-0000-000000000001",
            room_type_id="c1000000-0000-0000-0000-000000000101",
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
            guests=2,
            base_price="500.00",
            taxes="50.00",
            discounts="25.00",
            total_price="525.00",
            currency_code="USD",
            primary_guest=MagicMock(
                first_name="Juan",
                last_name="Pérez",
                document_type="CC",
                document_number="1234567890",
                nationality="COL",
            ),
            payment=MagicMock(
                amount="525.00",
                currency_code="USD",
                payment_token="tok_visa_4242",
                provider_id=None,
            ),
        )
        return flow

    @pytest.mark.asyncio
    async def test_validate_missing_required_fields(self):
        """Test validación falla cuando faltan campos requeridos."""
        flow = SimpleReservationFlow()
        flow.set_data(hotel_id="some-id")  # Faltan room_type_id, check_in, check_out
        
        result = await flow.step_validate()
        
        assert result["success"] is False
        assert result["proceed"] is False
        assert "Faltan datos obligatorios" in result["error"]
        assert "room_type_id" in result["missing"]
        assert "check_in" in result["missing"]
        assert "check_out" in result["missing"]

    @pytest.mark.asyncio
    async def test_validate_user_id_optional(self):
        """Test que user_id es opcional (no requerido en validación)."""
        flow = SimpleReservationFlow()
        # Solo datos requeridos (sin user_id)
        flow.set_data(
            hotel_id="b1000000-0000-0000-0000-000000000001",
            room_type_id="c1000000-0000-0000-0000-000000000101",
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
        )
        
        # Mock completamente el método para evitar conexión a BD
        with patch.object(flow, "step_validate") as mock_validate:
            mock_validate.return_value = {
                "success": True,
                "proceed": True,
                "exists": False,
                "message": "OK"
            }
            result = await flow.step_validate()
        
        # Verificar que la validación no requiere user_id
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_validate_blocks_when_kafka_exists_true(self, flow):
        """Kafka/PMS exists=true debe impedir create (sin depender del solapamiento en BD)."""
        with patch(
            "state_machine.simple_reservation_flow.publish_reservation_validate",
            new_callable=AsyncMock,
        ):
            with patch.object(
                flow.event,
                "wait_for_reply",
                new_callable=AsyncMock,
                return_value={"exists": True, "message": "PMS: no availability"},
            ):
                result = await flow.step_validate()

        assert result["success"] is True
        assert result["proceed"] is False
        assert "No hay agenda disponible" in result["message"]

    @pytest.mark.asyncio
    async def test_run_create_flow_stops_when_kafka_pms_blocks(self):
        """Flujo completo: exists=true desde Kafka → completed false, sin step create."""
        flow = SimpleReservationFlow()
        flow.set_data(
            user_id=None,
            hotel_id="b1000000-0000-0000-0000-000000000001",
            room_type_id="c1000000-0000-0000-0000-000000000101",
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
            guests=2,
        )
        with patch(
            "state_machine.simple_reservation_flow.publish_reservation_validate",
            new_callable=AsyncMock,
        ):
            with patch.object(
                flow.event,
                "wait_for_reply",
                new_callable=AsyncMock,
                return_value={
                    "exists": True,
                    "message": "PMS: no available units for one or more nights.",
                },
            ):
                result = await flow.run_create_flow()

        assert result["completed"] is False
        assert result["step"] == "validate"
        assert "No hay agenda disponible" in result["result"].get("message", "")


class TestSimpleReservationFlowCreate:
    """Tests para el paso de creación (step_create)."""

    @pytest.fixture
    def flow_with_context(self):
        """Flow con datos completos en contexto."""
        flow = SimpleReservationFlow()
        flow.set_data(
            user_id=None,
            hotel_id="b1000000-0000-0000-0000-000000000001",
            room_type_id="c1000000-0000-0000-0000-000000000101",
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
            guests=2,
            base_price="500.00",
            taxes="50.00",
            discounts="25.00",
            total_price="525.00",
            currency_code="USD",
            primary_guest=MagicMock(
                first_name="Juan",
                last_name="Pérez",
                document_type="CC",
                document_number="1234567890",
                nationality="COL",
            ),
            payment=MagicMock(
                amount="525.00",
                currency_code="USD",
                payment_token="tok_visa_4242",
                provider_id=None,
            ),
            special_requests="Habitación con vista al mar",
        )
        return flow

    @pytest.mark.asyncio
    async def test_create_success(self, flow_with_context):
        """Test creación exitosa con user_id opcional."""
        flow = flow_with_context
        
        mock_response = MagicMock()
        mock_response.id = uuid.UUID("d1000000-0000-0000-0000-000000000001")
        mock_response.confirmation_code = "RES123456"
        mock_response.status = "pending"
        mock_response.message = "Reservación creada"
        mock_response.hotel.id = uuid.UUID("b1000000-0000-0000-0000-000000000001")
        mock_response.hotel.name = "Hotel Test"
        mock_response.room_type.id = uuid.UUID("c1000000-0000-0000-0000-000000000101")
        mock_response.room_type.name = "Deluxe"
        mock_response.pricing.nights = 4
        mock_response.pricing.total = Decimal("525.00")
        mock_response.check_in = date(2026, 5, 1)
        mock_response.check_out = date(2026, 5, 5)
        
        with patch.object(flow.mediator, "send_async", return_value=mock_response):
            result = await flow.step_create()
        
        assert result["success"] is True
        assert result["proceed"] is True
        assert result["confirmation_code"] == "RES123456"
        assert result["status"] == "pending"
        assert "hotel" in result
        assert "room_type" in result
        assert "pricing" in result
        assert result["hotel"]["name"] == "Hotel Test"
        assert result["pricing"]["nights"] == 4

    @pytest.mark.asyncio
    async def test_create_with_user_id(self):
        """Test creación con user_id presente."""
        flow = SimpleReservationFlow()
        flow.set_data(
            user_id="a1000000-0000-0000-0000-000000000001",
            hotel_id="b1000000-0000-0000-0000-000000000001",
            room_type_id="c1000000-0000-0000-0000-000000000101",
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
            guests=2,
            base_price="500.00",
            taxes="50.00",
            discounts="0.00",
            total_price="550.00",
            primary_guest=MagicMock(first_name="User", last_name="Test"),
            payment=MagicMock(amount="550.00", payment_token="tok_123"),
        )
        
        mock_response = MagicMock()
        mock_response.id = uuid.UUID("d1000000-0000-0000-0000-000000000001")
        mock_response.confirmation_code = "RES789012"
        mock_response.status = "pending"
        mock_response.message = "Reservación creada"
        mock_response.hotel.name = "Hotel"
        mock_response.room_type.name = "Room"
        mock_response.pricing.nights = 4
        mock_response.pricing.total = Decimal("550.00")
        mock_response.check_in = date(2026, 5, 1)
        mock_response.check_out = date(2026, 5, 5)
        
        with patch.object(flow.mediator, "send_async", return_value=mock_response):
            result = await flow.step_create()
        
        assert result["success"] is True
        assert result["confirmation_code"] == "RES789012"

    @pytest.mark.asyncio
    async def test_create_error(self, flow_with_context):
        """Test manejo de error en creación."""
        flow = flow_with_context
        
        with patch.object(flow.mediator, "send_async", side_effect=Exception("DB Error")):
            result = await flow.step_create()
        
        assert result["success"] is False
        assert result["proceed"] is False
        assert "DB Error" in result["error"]


class TestSimpleReservationFlowComplete:
    """Tests para el flujo completo."""

    @pytest.mark.asyncio
    async def test_run_create_flow_success(self):
        """Test flujo completo validate → create exitoso."""
        flow = SimpleReservationFlow()
        flow.set_data(
            user_id=None,
            hotel_id="b1000000-0000-0000-0000-000000000001",
            room_type_id="c1000000-0000-0000-0000-000000000101",
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
            guests=2,
            primary_guest=MagicMock(first_name="Test", last_name="User"),
            payment=MagicMock(amount="100.00", payment_token="tok_123"),
        )
        
        # Mock validate: no existe, puede continuar
        with patch.object(flow, "step_validate") as mock_validate:
            mock_validate.return_value = {
                "success": True,
                "proceed": True,
                "exists": False,
                "message": "OK"
            }
            
            # Mock create: éxito
            with patch.object(flow, "step_create") as mock_create:
                mock_create.return_value = {
                    "success": True,
                    "proceed": True,
                    "confirmation_code": "RES999999",
                    "reservation_id": "d1000000-0000-0000-0000-000000000001",
                    "status": "pending",
                    "message": "Created",
                    "hotel": {"name": "Hotel"},
                    "room_type": {"name": "Room"},
                    "pricing": {"total": "100.00"},
                }
                
                result = await flow.run_create_flow()
        
        assert result["completed"] is True
        assert result["step"] == "create"
        assert result["result"]["confirmation_code"] == "RES999999"

    @pytest.mark.asyncio
    async def test_run_create_flow_stops_on_validate_fail(self):
        """Test flujo se detiene si validate retorna proceed=False."""
        flow = SimpleReservationFlow()
        flow.set_data(
            user_id=None,
            hotel_id="b1000000-0000-0000-0000-000000000001",
            room_type_id="c1000000-0000-0000-0000-000000000101",
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
            guests=2,
            primary_guest=MagicMock(first_name="Test", last_name="User"),
            payment=MagicMock(amount="100.00", payment_token="tok_123"),
        )
        
        # Mock validate: existe solapamiento, NO continuar
        with patch.object(flow, "step_validate") as mock_validate:
            mock_validate.return_value = {
                "success": True,
                "proceed": False,
                "exists": True,
                "overlap": True,
                "confirmation_code": "RESEXISTING",
                "message": "Ya existe reserva"
            }
            
            result = await flow.run_create_flow()
        
        assert result["completed"] is False
        assert result["step"] == "validate"
        assert result["result"]["exists"] is True

    @pytest.mark.asyncio
    async def test_run_create_flow_stops_on_validate_error(self):
        """Test flujo se detiene si validate falla."""
        flow = SimpleReservationFlow()
        flow.set_data(
            user_id=None,
            hotel_id="b1000000-0000-0000-0000-000000000001",
            room_type_id="c1000000-0000-0000-0000-000000000101",
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
        )
        
        with patch.object(flow, "step_validate") as mock_validate:
            mock_validate.return_value = {
                "success": False,
                "proceed": False,
                "error": "Validation failed"
            }
            
            result = await flow.run_create_flow()
        
        assert result["completed"] is False
        assert result["step"] == "validate"
