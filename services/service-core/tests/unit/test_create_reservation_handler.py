"""
Tests unitarios para el handler de creación de reservaciones.
"""
import uuid
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from reservation_service.commands.reservation_commands import (
    CreateReservationCommand,
    CreateReservationResponse,
    HotelInfo,
    RoomTypeInfo,
    PricingDetails,
)


class TestCreateReservationHandler:
    """Tests para handle_create_reservation."""

    @pytest.fixture
    def base_command(self):
        """Comando base para tests."""
        return CreateReservationCommand(
            hotel_id=uuid.UUID("b1000000-0000-0000-0000-000000000001"),
            room_type_id=uuid.UUID("c1000000-0000-0000-0000-000000000101"),
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
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
            guests=2,
            base_price=Decimal("500.00"),
            taxes=Decimal("50.00"),
            discounts=Decimal("25.00"),
            total_price=Decimal("525.00"),
            currency_code="USD",
            user_id=None,
        )

    @pytest.fixture
    def mock_hotel(self):
        """Mock de hotel."""
        hotel = MagicMock()
        hotel.id = uuid.UUID("b1000000-0000-0000-0000-000000000001")
        hotel.name = "Hotel Test"
        hotel.description = "Un hotel de prueba"
        hotel.address = "Calle 123"
        hotel.city = "Bogotá"
        hotel.stars = 4
        hotel.rating = Decimal("4.5")
        return hotel

    @pytest.fixture
    def mock_room_type(self):
        """Mock de room_type."""
        room = MagicMock()
        room.id = uuid.UUID("c1000000-0000-0000-0000-000000000101")
        room.name = "Habitación Deluxe"
        room.description = "Habitación espaciosa"
        room.max_capacity = 2
        room.bed_type = "King"
        room.size_sqm = Decimal("35.0")
        return room

    def test_nights_calculation(self, base_command):
        """Test cálculo de noches."""
        # 4 noches: 1 Mayo al 5 Mayo
        nights = (base_command.check_out - base_command.check_in).days
        assert nights == 4
        
        # Caso edge: mismo día
        base_command.check_out = base_command.check_in
        nights = (base_command.check_out - base_command.check_in).days
        assert nights == 0
        
    def test_generate_confirmation_code(self):
        """Test generación de código de confirmación."""
        from reservation_service.commands.create_reservation_handler import generate_confirmation_code
        
        code = generate_confirmation_code()
        
        assert code.startswith("RES")
        assert len(code) == 11  # RES + 8 caracteres
        assert code[3:].isalnum()

    def test_command_structure(self, base_command):
        """Test estructura del comando de creación."""
        # Verificar campos requeridos
        assert base_command.hotel_id is not None
        assert base_command.room_type_id is not None
        assert base_command.check_in is not None
        assert base_command.check_out is not None
        assert base_command.primary_guest is not None
        assert base_command.payment is not None
        
        # Verificar campos opcionales con defaults
        assert base_command.guests == 2
        assert base_command.currency_code == "USD"
        assert base_command.user_id is None  # Guest reservation

    def test_pricing_calculation(self, base_command):
        """Test cálculo de precios."""
        # Calcular precio total esperado
        expected_total = base_command.base_price + base_command.taxes - base_command.discounts
        assert expected_total == Decimal("525.00")
        assert base_command.total_price == expected_total
        
        # Precio por noche
        nights = 4
        price_per_night = base_command.total_price / nights
        assert price_per_night == Decimal("131.25")


class TestCreateReservationResponse:
    """Tests para la estructura de respuesta."""

    def test_response_structure(self):
        """Test que la respuesta tiene la estructura enriquecida."""
        from uuid import uuid4
        
        response = CreateReservationResponse(
            id=uuid4(),
            user_id=None,
            confirmation_code="RES123456",
            status="pending",
            message="Reservación creada exitosamente",
            hotel=HotelInfo(
                id=uuid4(),
                name="Hotel Test",
                description="Un hotel",
                address="Calle 123",
                city="Bogotá",
                stars=4,
                rating=Decimal("4.5")
            ),
            room_type=RoomTypeInfo(
                id=uuid4(),
                name="Deluxe",
                description="Habitación deluxe",
                max_capacity=2,
                bed_type="King",
                size_sqm=Decimal("35.0")
            ),
            pricing=PricingDetails(
                nights=4,
                guests=2,
                price_per_night=Decimal("131.25"),
                subtotal=Decimal("525.00"),
                taxes=Decimal("50.00"),
                discounts=Decimal("25.00"),
                total=Decimal("525.00"),
                currency_code="USD"
            ),
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
        )
        
        # Verificar estructura
        assert response.confirmation_code.startswith("RES")
        assert response.user_id is None
        
        # Hotel info
        assert response.hotel.name == "Hotel Test"
        assert response.hotel.stars == 4
        assert response.hotel.rating == Decimal("4.5")
        
        # Room info
        assert response.room_type.name == "Deluxe"
        assert response.room_type.max_capacity == 2
        assert response.room_type.bed_type == "King"
        
        # Pricing
        assert response.pricing.nights == 4
        assert response.pricing.guests == 2
        assert response.pricing.price_per_night == Decimal("131.25")
        assert response.pricing.subtotal == Decimal("525.00")
        assert response.pricing.taxes == Decimal("50.00")
        assert response.pricing.discounts == Decimal("25.00")
        assert response.pricing.total == Decimal("525.00")


class TestReservationFlowIntegration:
    """Tests de integración básica del flujo."""

    @pytest.mark.asyncio
    async def test_flow_with_user_id(self):
        """Test flujo completo con usuario logueado."""
        from state_machine.simple_reservation_flow import SimpleReservationFlow
        
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
        
        # Mock del mediator para step_create
        mock_response = MagicMock()
        mock_response.id = uuid.UUID("d1000000-0000-0000-0000-000000000001")
        mock_response.confirmation_code = "RESUSER001"
        mock_response.status = "pending"
        mock_response.message = "Created with user"
        mock_response.hotel.name = "Hotel"
        mock_response.room_type.name = "Room"
        mock_response.pricing.nights = 4
        mock_response.pricing.total = Decimal("550.00")
        mock_response.check_in = date(2026, 5, 1)
        mock_response.check_out = date(2026, 5, 5)
        
        with patch.object(flow.mediator, "send_async", return_value=mock_response):
            result = await flow.step_create()
        
        assert result["success"] is True
        assert result["confirmation_code"] == "RESUSER001"

    @pytest.mark.asyncio
    async def test_flow_without_user_id(self):
        """Test flujo completo sin usuario (guest)."""
        from state_machine.simple_reservation_flow import SimpleReservationFlow
        
        flow = SimpleReservationFlow()
        flow.set_data(
            user_id=None,  # Guest
            hotel_id="b1000000-0000-0000-0000-000000000001",
            room_type_id="c1000000-0000-0000-0000-000000000101",
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 5),
            guests=2,
            base_price="500.00",
            taxes="50.00",
            discounts="25.00",
            total_price="525.00",
            primary_guest=MagicMock(first_name="Guest", last_name="User"),
            payment=MagicMock(amount="525.00", payment_token="tok_guest"),
        )
        
        mock_response = MagicMock()
        mock_response.id = uuid.UUID("d1000000-0000-0000-0000-000000000002")
        mock_response.confirmation_code = "RESGUEST01"
        mock_response.status = "pending"
        mock_response.message = "Created for guest"
        mock_response.hotel.name = "Hotel"
        mock_response.room_type.name = "Room"
        mock_response.pricing.nights = 4
        mock_response.pricing.total = Decimal("525.00")
        mock_response.check_in = date(2026, 5, 1)
        mock_response.check_out = date(2026, 5, 5)
        
        with patch.object(flow.mediator, "send_async", return_value=mock_response):
            result = await flow.step_create()
        
        assert result["success"] is True
        assert result["confirmation_code"] == "RESGUEST01"
