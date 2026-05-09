"""
Tests unitarios para el router de administración de hotel.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from routes.hotel_admin_router import router as hotel_admin_router
from infrastructure.database import get_session
from user_service.utils.security import get_current_user


@pytest.fixture
def client_hotel_admin():
    app = FastAPI()
    app.include_router(hotel_admin_router)

    async def mock_current_user():
        return {
            "user_id": "a2000000-0000-0000-0000-000000000001",
            "email": "admin@hotel.com",
            "user_type": "hotel_admin",
            "hotel_id": "b1000000-0000-0000-0000-000000000001",
        }

    app.dependency_overrides[get_current_user] = mock_current_user
    app.dependency_overrides[get_session] = lambda: AsyncMock()
    return TestClient(app)


@pytest.fixture
def client_traveler():
    app = FastAPI()
    app.include_router(hotel_admin_router)

    async def mock_current_user():
        return {
            "user_id": "a2000000-0000-0000-0000-000000000002",
            "email": "traveler@example.com",
            "user_type": "traveler",
        }

    app.dependency_overrides[get_current_user] = mock_current_user
    app.dependency_overrides[get_session] = lambda: AsyncMock()
    return TestClient(app)


@pytest.fixture
def client_no_auth():
    app = FastAPI()
    app.include_router(hotel_admin_router)
    return TestClient(app)


def mock_reservation(**kwargs):
    defaults = {
        "id": uuid.UUID("d1000000-0000-0000-0000-000000000001"),
        "user_id": uuid.UUID("a2000000-0000-0000-0000-000000000001"),
        "hotel_id": uuid.UUID("b1000000-0000-0000-0000-000000000001"),
        "room_type_id": uuid.UUID("c1000000-0000-0000-0000-000000000101"),
        "cart_id": None,
        "check_in": date(2026, 5, 1),
        "check_out": date(2026, 5, 5),
        "guests": 2,
        "base_price": Decimal("500.00"),
        "taxes": Decimal("50.00"),
        "discounts": Decimal("0.00"),
        "total_price": Decimal("550.00"),
        "currency_code": "USD",
        "status": "confirmed",
        "cancellation_policy": None,
        "special_requests": None,
        "confirmation_code": "RES001",
        "created_at": datetime(2026, 1, 1, 12, 0, 0),
        "updated_at": None,
    }
    defaults.update(kwargs)
    return MagicMockObject(**defaults)


def mock_room_type(**kwargs):
    defaults = {
        "id": uuid.UUID("c1000000-0000-0000-0000-000000000101"),
        "hotel_id": uuid.UUID("b1000000-0000-0000-0000-000000000001"),
        "name": "Deluxe",
        "description": "Habitación deluxe con vista al mar",
        "base_price": Decimal("150.00"),
        "max_capacity": 2,
        "bed_type": "King",
        "size_sqm": Decimal("35.0"),
        "total_units": 10,
        "active": True,
        "created_at": datetime(2025, 1, 1, 12, 0, 0),
        "updated_at": datetime(2025, 1, 1, 12, 0, 0),
    }
    defaults.update(kwargs)
    return MagicMockObject(**defaults)


class TestHotelAdminReservationsList:
    """Tests para GET /hotel-admin/reservations"""

    def test_list_success(self, client_hotel_admin):
        res = mock_reservation()
        room = mock_room_type()

        with patch(
            "routes.hotel_admin_router.ReservationRepository"
        ) as MockRepo:
            mock_instance = MockRepo.return_value
            mock_instance.list_by_date_range_with_room_type = AsyncMock(return_value=[(res, room)])

            response = client_hotel_admin.get(
                "/hotel-admin/reservations",
                params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "confirmed"
        assert data["items"][0]["room_type"]["name"] == "Deluxe"
        assert data["items"][0]["room_type"]["description"] == "Habitación deluxe con vista al mar"
        assert data["items"][0]["room_type"]["max_capacity"] == 2
        assert data["items"][0]["room_type"]["bed_type"] == "King"

    def test_list_with_status_filter(self, client_hotel_admin):
        res = mock_reservation(status="pending")
        room = mock_room_type()

        with patch(
            "routes.hotel_admin_router.ReservationRepository"
        ) as MockRepo:
            mock_instance = MockRepo.return_value
            mock_instance.list_by_date_range_with_room_type = AsyncMock(return_value=[(res, room)])

            response = client_hotel_admin.get(
                "/hotel-admin/reservations",
                params={"start_date": "2026-01-01", "end_date": "2026-01-31", "status": "pending"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        mock_instance.list_by_date_range_with_room_type.assert_awaited_once_with(
            date(2026, 1, 1), date(2026, 1, 31), "pending", uuid.UUID("b1000000-0000-0000-0000-000000000001")
        )

    def test_list_invalid_status(self, client_hotel_admin):
        response = client_hotel_admin.get(
            "/hotel-admin/reservations",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31", "status": "invalid"},
        )
        assert response.status_code == 400
        assert "Estado inválido" in response.json()["detail"]

    def test_list_invalid_date_range(self, client_hotel_admin):
        response = client_hotel_admin.get(
            "/hotel-admin/reservations",
            params={"start_date": "2026-02-01", "end_date": "2026-01-01"},
        )
        assert response.status_code == 400
        assert "start_date no puede ser mayor" in response.json()["detail"]

    def test_list_forbidden_for_traveler(self, client_traveler):
        response = client_traveler.get(
            "/hotel-admin/reservations",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        )
        assert response.status_code == 403
        assert "Acceso denegado" in response.json()["detail"]

    def test_list_unauthorized(self, client_no_auth):
        response = client_no_auth.get(
            "/hotel-admin/reservations",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        )
        assert response.status_code == 403


class TestHotelAdminRoomTypesList:
    """Tests para GET /hotel-admin/room-types"""

    def test_list_room_types_success(self, client_hotel_admin):
        room_type = mock_room_type()
        amenity = MagicMockObject(
            id=uuid.UUID("f1000000-0000-0000-0000-000000000001"),
            room_type_id=room_type.id,
            name="Wi-Fi",
            icon="wifi",
        )
        image = MagicMockObject(
            id=uuid.UUID("f2000000-0000-0000-0000-000000000001"),
            room_type_id=room_type.id,
            url="https://example.com/image.jpg",
            alt_text="Room image",
            sort_order=1,
        )

        with patch(
            "routes.hotel_admin_router.RoomTypeRepository"
        ) as MockRepo:
            mock_instance = MockRepo.return_value
            mock_instance.list_by_hotel_id = AsyncMock(return_value=[
                MagicMockObject(room_type=room_type, amenities=[amenity], images=[image])
            ])

            response = client_hotel_admin.get(
                "/hotel-admin/room-types",
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Deluxe"
        assert data["items"][0]["amenities"][0]["name"] == "Wi-Fi"
        assert data["items"][0]["images"][0]["url"] == "https://example.com/image.jpg"

    def test_list_room_types_include_inactive(self, client_hotel_admin):
        room_type = mock_room_type(active=False)

        with patch(
            "routes.hotel_admin_router.RoomTypeRepository"
        ) as MockRepo:
            mock_instance = MockRepo.return_value
            mock_instance.list_by_hotel_id = AsyncMock(return_value=[
                MagicMockObject(room_type=room_type, amenities=[], images=[])
            ])

            response = client_hotel_admin.get(
                "/hotel-admin/room-types?include_inactive=true",
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        mock_instance.list_by_hotel_id.assert_awaited_once_with(
            uuid.UUID("b1000000-0000-0000-0000-000000000001"), active_only=False
        )

    def test_list_room_types_forbidden_for_traveler(self, client_traveler):
        response = client_traveler.get(
            "/hotel-admin/room-types",
        )
        assert response.status_code == 403
        assert "Acceso denegado" in response.json()["detail"]


class TestHotelAdminInventoryCalendar:
    """Tests para GET /hotel-admin/inventory-calendar"""

    def test_list_inventory_success(self, client_hotel_admin):
        mock_items = [
            MagicMockInventoryCalendar(
                id=uuid.UUID("e1000000-0000-0000-0000-000000000001"),
                room_type_id=uuid.UUID("c1000000-0000-0000-0000-000000000101"),
                date="2026-05-01",
                available_units=5,
                price_per_night=150.00,
                currency_code="USD",
                minimum_stay=2,
            ),
            MagicMockInventoryCalendar(
                id=uuid.UUID("e1000000-0000-0000-0000-000000000002"),
                room_type_id=uuid.UUID("c1000000-0000-0000-0000-000000000101"),
                date="2026-05-02",
                available_units=3,
                price_per_night=150.00,
                currency_code="USD",
                minimum_stay=2,
            ),
        ]

        with patch(
            "routes.hotel_admin_router.InventoryCalendarRepository"
        ) as MockRepo:
            mock_instance = MockRepo.return_value
            mock_instance.list_available_by_date_range = AsyncMock(return_value=mock_items)

            response = client_hotel_admin.get(
                "/hotel-admin/inventory-calendar",
                params={"start_date": "2026-05-01", "end_date": "2026-05-02"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["available_units"] == 5

    def test_list_inventory_with_room_type_filter(self, client_hotel_admin):
        target_room = uuid.UUID("c1000000-0000-0000-0000-000000000101")
        mock_items = [
            MagicMockInventoryCalendar(
                id=uuid.UUID("e1000000-0000-0000-0000-000000000001"),
                room_type_id=target_room,
                date="2026-05-01",
                available_units=2,
                price_per_night=200.00,
                currency_code="USD",
                minimum_stay=1,
            ),
        ]

        with patch(
            "routes.hotel_admin_router.InventoryCalendarRepository"
        ) as MockRepo:
            mock_instance = MockRepo.return_value
            mock_instance.list_available_by_date_range = AsyncMock(return_value=mock_items)

            response = client_hotel_admin.get(
                "/hotel-admin/inventory-calendar",
                params={
                    "start_date": "2026-05-01",
                    "end_date": "2026-05-01",
                    "room_type_id": str(target_room),
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        MockRepo.return_value.list_available_by_date_range.assert_awaited_once_with(
            date(2026, 5, 1), date(2026, 5, 1), target_room, uuid.UUID("b1000000-0000-0000-0000-000000000001")
        )

    def test_list_inventory_invalid_date_range(self, client_hotel_admin):
        response = client_hotel_admin.get(
            "/hotel-admin/inventory-calendar",
            params={"start_date": "2026-02-01", "end_date": "2026-01-01"},
        )
        assert response.status_code == 400

    def test_list_inventory_forbidden_for_traveler(self, client_traveler):
        response = client_traveler.get(
            "/hotel-admin/inventory-calendar",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
        )
        assert response.status_code == 403
        assert "Acceso denegado" in response.json()["detail"]


class MagicMockObject:
    """Helper para crear mocks con atributos dinámicos."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MagicMockInventoryCalendar:
    """Helper para crear mocks con atributos de InventoryCalendar."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# Tests para nuevos endpoints de tarifas / inventario (autorización owner_user_id)
# ---------------------------------------------------------------------------

class TestHotelAdminRoomsSimple:
    """Tests para GET /hotel-admin/rooms/simple"""

    def test_list_rooms_simple_success(self, client_hotel_admin):
        mock_rooms = [
            mock_room_type(id=uuid.UUID("c1000000-0000-0000-0000-000000000101"), name="Deluxe"),
            mock_room_type(id=uuid.UUID("c1000000-0000-0000-0000-000000000102"), name="Standard"),
        ]

        with patch("routes.hotel_admin_router._get_owned_hotel_id", new=AsyncMock(return_value=uuid.UUID("b1000000-0000-0000-0000-000000000001"))):
            with patch("routes.hotel_admin_router.RoomTypeRepository") as MockRepo:
                mock_instance = MockRepo.return_value
                mock_instance.list_simple_by_hotel_id = AsyncMock(return_value=mock_rooms)

                response = client_hotel_admin.get("/hotel-admin/rooms/simple")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["items"][0]["name"] == "Deluxe"
        assert data["items"][0]["description"] == "Habitación deluxe con vista al mar"
        assert "id" in data["items"][0]

    def test_list_rooms_simple_forbidden_traveler(self, client_traveler):
        response = client_traveler.get("/hotel-admin/rooms/simple")
        assert response.status_code == 403
        assert "Acceso denegado" in response.json()["detail"]

    def test_list_rooms_simple_unauthorized(self, client_no_auth):
        response = client_no_auth.get("/hotel-admin/rooms/simple")
        assert response.status_code == 403


class TestHotelAdminRoomDetail:
    """Tests para GET /hotel-admin/rooms/{room_id}"""

    def test_get_room_detail_success(self, client_hotel_admin):
        room_type = mock_room_type()
        amenity = MagicMockObject(
            id=uuid.UUID("f1000000-0000-0000-0000-000000000001"),
            room_type_id=room_type.id,
            name="Wi-Fi",
            icon="wifi",
        )
        image = MagicMockObject(
            id=uuid.UUID("f2000000-0000-0000-0000-000000000001"),
            room_type_id=room_type.id,
            url="https://example.com/image.jpg",
            alt_text="Room image",
            sort_order=1,
        )

        with patch("routes.hotel_admin_router._get_owned_hotel_id", new=AsyncMock(return_value=uuid.UUID("b1000000-0000-0000-0000-000000000001"))):
            with patch("routes.hotel_admin_router.RoomTypeRepository") as MockRepo:
                mock_instance = MockRepo.return_value
                mock_instance.get_by_id = AsyncMock(return_value=room_type)
                mock_instance.list_by_hotel_id = AsyncMock(return_value=[
                    MagicMockObject(room_type=room_type, amenities=[amenity], images=[image])
                ])

                response = client_hotel_admin.get(f"/hotel-admin/rooms/{room_type.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Deluxe"
        assert data["hotel_id"] == str(room_type.hotel_id)
        assert len(data["amenities"]) == 1
        assert data["amenities"][0]["name"] == "Wi-Fi"

    def test_get_room_detail_not_found(self, client_hotel_admin):
        other_room = mock_room_type(hotel_id=uuid.UUID("b1000000-0000-0000-0000-000000000999"))

        with patch("routes.hotel_admin_router._get_owned_hotel_id", new=AsyncMock(return_value=uuid.UUID("b1000000-0000-0000-0000-000000000001"))):
            with patch("routes.hotel_admin_router.RoomTypeRepository") as MockRepo:
                mock_instance = MockRepo.return_value
                mock_instance.get_by_id = AsyncMock(return_value=other_room)

                response = client_hotel_admin.get(f"/hotel-admin/rooms/{other_room.id}")

        assert response.status_code == 404
        assert "Habitación no encontrada" in response.json()["detail"]

    def test_get_room_detail_forbidden_traveler(self, client_traveler):
        response = client_traveler.get(f"/hotel-admin/rooms/{uuid.UUID('c1000000-0000-0000-0000-000000000101')}")
        assert response.status_code == 403


class TestHotelAdminRoomCalendar:
    """Tests para GET /hotel-admin/rooms/{room_id}/calendar"""

    def test_get_room_calendar_success(self, client_hotel_admin):
        room_type = mock_room_type()
        mock_items = [
            MagicMockInventoryCalendar(
                id=uuid.UUID("e1000000-0000-0000-0000-000000000001"),
                room_type_id=room_type.id,
                date="2026-05-01",
                available_units=5,
                price_per_night=150.00,
                currency_code="USD",
                minimum_stay=2,
            ),
        ]

        with patch("routes.hotel_admin_router._get_owned_hotel_id", new=AsyncMock(return_value=uuid.UUID("b1000000-0000-0000-0000-000000000001"))):
            with patch("routes.hotel_admin_router.RoomTypeRepository") as MockRoomRepo:
                mock_room_instance = MockRoomRepo.return_value
                mock_room_instance.get_by_id = AsyncMock(return_value=room_type)

                with patch("routes.hotel_admin_router.InventoryCalendarRepository") as MockInvRepo:
                    mock_inv_instance = MockInvRepo.return_value
                    mock_inv_instance.list_by_date_range = AsyncMock(return_value=mock_items)

                    response = client_hotel_admin.get(
                        f"/hotel-admin/rooms/{room_type.id}/calendar",
                        params={"start_date": "2026-05-01", "end_date": "2026-05-01"},
                    )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["available_units"] == 5

    def test_get_room_calendar_invalid_date_range(self, client_hotel_admin):
        room_type = mock_room_type()

        with patch("routes.hotel_admin_router._get_owned_hotel_id", new=AsyncMock(return_value=uuid.UUID("b1000000-0000-0000-0000-000000000001"))):
            with patch("routes.hotel_admin_router.RoomTypeRepository") as MockRoomRepo:
                mock_room_instance = MockRoomRepo.return_value
                mock_room_instance.get_by_id = AsyncMock(return_value=room_type)

                response = client_hotel_admin.get(
                    f"/hotel-admin/rooms/{room_type.id}/calendar",
                    params={"start_date": "2026-05-02", "end_date": "2026-05-01"},
                )

        assert response.status_code == 400

    def test_get_room_calendar_room_not_found(self, client_hotel_admin):
        with patch("routes.hotel_admin_router._get_owned_hotel_id", new=AsyncMock(return_value=uuid.UUID("b1000000-0000-0000-0000-000000000001"))):
            with patch("routes.hotel_admin_router.RoomTypeRepository") as MockRoomRepo:
                mock_room_instance = MockRoomRepo.return_value
                mock_room_instance.get_by_id = AsyncMock(return_value=None)

                response = client_hotel_admin.get(
                    "/hotel-admin/rooms/c1000000-0000-0000-0000-000000000999/calendar",
                    params={"start_date": "2026-05-01", "end_date": "2026-05-01"},
                )

        assert response.status_code == 404


class TestHotelAdminUpdateInventory:
    """Tests para PATCH /hotel-admin/inventory/{inventory_id}"""

    def test_update_inventory_success(self, client_hotel_admin):
        room_type = mock_room_type()
        inventory_item = MagicMockInventoryCalendar(
            id=uuid.UUID("e1000000-0000-0000-0000-000000000001"),
            room_type_id=room_type.id,
            date="2026-05-01",
            available_units=10,
            price_per_night=200.00,
            currency_code="USD",
            minimum_stay=1,
        )
        updated_item = MagicMockInventoryCalendar(
            id=inventory_item.id,
            room_type_id=room_type.id,
            date="2026-05-01",
            available_units=5,
            price_per_night=250.00,
            currency_code="USD",
            minimum_stay=1,
        )

        with patch("routes.hotel_admin_router._get_owned_hotel_id", new=AsyncMock(return_value=uuid.UUID("b1000000-0000-0000-0000-000000000001"))):
            with patch("routes.hotel_admin_router.InventoryCalendarRepository") as MockInvRepo:
                mock_inv_instance = MockInvRepo.return_value
                mock_inv_instance.get_by_id = AsyncMock(return_value=inventory_item)
                mock_inv_instance.update = AsyncMock(return_value=updated_item)

                with patch("routes.hotel_admin_router.RoomTypeRepository") as MockRoomRepo:
                    mock_room_instance = MockRoomRepo.return_value
                    mock_room_instance.get_by_id = AsyncMock(return_value=room_type)

                    response = client_hotel_admin.patch(
                        f"/hotel-admin/inventory/{inventory_item.id}",
                        json={"available_units": 5, "price_per_night": "250.00"},
                    )

        assert response.status_code == 200
        data = response.json()
        assert data["available_units"] == 5
        assert float(data["price_per_night"]) == 250.00

    def test_update_inventory_not_found(self, client_hotel_admin):
        with patch("routes.hotel_admin_router._get_owned_hotel_id", new=AsyncMock(return_value=uuid.UUID("b1000000-0000-0000-0000-000000000001"))):
            with patch("routes.hotel_admin_router.InventoryCalendarRepository") as MockInvRepo:
                mock_inv_instance = MockInvRepo.return_value
                mock_inv_instance.get_by_id = AsyncMock(return_value=None)

                response = client_hotel_admin.patch(
                    "/hotel-admin/inventory/e1000000-0000-0000-0000-000000000999",
                    json={"available_units": 5, "price_per_night": "250.00"},
                )

        assert response.status_code == 404
        assert "Registro de inventario no encontrado" in response.json()["detail"]

    def test_update_inventory_forbidden_wrong_room(self, client_hotel_admin):
        other_room = mock_room_type(hotel_id=uuid.UUID("b1000000-0000-0000-0000-000000000999"))
        inventory_item = MagicMockInventoryCalendar(
            id=uuid.UUID("e1000000-0000-0000-0000-000000000001"),
            room_type_id=other_room.id,
            date="2026-05-01",
            available_units=10,
            price_per_night=200.00,
            currency_code="USD",
            minimum_stay=1,
        )

        with patch("routes.hotel_admin_router._get_owned_hotel_id", new=AsyncMock(return_value=uuid.UUID("b1000000-0000-0000-0000-000000000001"))):
            with patch("routes.hotel_admin_router.InventoryCalendarRepository") as MockInvRepo:
                mock_inv_instance = MockInvRepo.return_value
                mock_inv_instance.get_by_id = AsyncMock(return_value=inventory_item)

                with patch("routes.hotel_admin_router.RoomTypeRepository") as MockRoomRepo:
                    mock_room_instance = MockRoomRepo.return_value
                    mock_room_instance.get_by_id = AsyncMock(return_value=other_room)

                    response = client_hotel_admin.patch(
                        f"/hotel-admin/inventory/{inventory_item.id}",
                        json={"available_units": 5, "price_per_night": "250.00"},
                    )

        assert response.status_code == 403
        assert "No tiene permiso" in response.json()["detail"]


class TestHotelAdminBulkInventory:
    """Tests para POST /hotel-admin/inventory/bulk"""

    def test_bulk_inventory_success(self, client_hotel_admin):
        room_type = mock_room_type()
        mock_items = [
            MagicMockInventoryCalendar(
                id=uuid.UUID("e1000000-0000-0000-0000-000000000001"),
                room_type_id=room_type.id,
                date="2026-05-01",
                available_units=8,
                price_per_night=180.00,
                currency_code="USD",
                minimum_stay=1,
            ),
            MagicMockInventoryCalendar(
                id=uuid.UUID("e1000000-0000-0000-0000-000000000002"),
                room_type_id=room_type.id,
                date="2026-05-02",
                available_units=8,
                price_per_night=180.00,
                currency_code="USD",
                minimum_stay=1,
            ),
        ]

        with patch("routes.hotel_admin_router._get_owned_hotel_id", new=AsyncMock(return_value=uuid.UUID("b1000000-0000-0000-0000-000000000001"))):
            with patch("routes.hotel_admin_router.RoomTypeRepository") as MockRoomRepo:
                mock_room_instance = MockRoomRepo.return_value
                mock_room_instance.get_by_id = AsyncMock(return_value=room_type)

                with patch("routes.hotel_admin_router.InventoryCalendarRepository") as MockInvRepo:
                    mock_inv_instance = MockInvRepo.return_value
                    mock_inv_instance.create_range = AsyncMock(return_value=mock_items)

                    response = client_hotel_admin.post(
                        "/hotel-admin/inventory/bulk",
                        json={
                            "room_type_id": str(room_type.id),
                            "start_date": "2026-05-01",
                            "end_date": "2026-05-02",
                            "available_units": 8,
                            "price_per_night": "180.00",
                            "currency_code": "USD",
                            "minimum_stay": 1,
                        },
                    )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["items"][0]["available_units"] == 8

    def test_bulk_inventory_conflict_existing_dates(self, client_hotel_admin):
        room_type = mock_room_type()

        with patch("routes.hotel_admin_router._get_owned_hotel_id", new=AsyncMock(return_value=uuid.UUID("b1000000-0000-0000-0000-000000000001"))):
            with patch("routes.hotel_admin_router.RoomTypeRepository") as MockRoomRepo:
                mock_room_instance = MockRoomRepo.return_value
                mock_room_instance.get_by_id = AsyncMock(return_value=room_type)

                with patch("routes.hotel_admin_router.InventoryCalendarRepository") as MockInvRepo:
                    mock_inv_instance = MockInvRepo.return_value
                    mock_inv_instance.create_range = AsyncMock(return_value=None)

                    response = client_hotel_admin.post(
                        "/hotel-admin/inventory/bulk",
                        json={
                            "room_type_id": str(room_type.id),
                            "start_date": "2026-05-01",
                            "end_date": "2026-05-02",
                            "available_units": 8,
                            "price_per_night": "180.00",
                        },
                    )

        assert response.status_code == 409
        assert "Ya existen registros" in response.json()["detail"]

    def test_bulk_inventory_invalid_date_range(self, client_hotel_admin):
        room_type = mock_room_type()

        with patch("routes.hotel_admin_router._get_owned_hotel_id", new=AsyncMock(return_value=uuid.UUID("b1000000-0000-0000-0000-000000000001"))):
            with patch("routes.hotel_admin_router.RoomTypeRepository") as MockRoomRepo:
                mock_room_instance = MockRoomRepo.return_value
                mock_room_instance.get_by_id = AsyncMock(return_value=room_type)

                response = client_hotel_admin.post(
                    "/hotel-admin/inventory/bulk",
                    json={
                        "room_type_id": str(room_type.id),
                        "start_date": "2026-05-02",
                        "end_date": "2026-05-01",
                        "available_units": 8,
                        "price_per_night": "180.00",
                    },
                )

        assert response.status_code == 400
        assert "end_date no puede ser menor" in response.json()["detail"]

    def test_bulk_inventory_room_not_found(self, client_hotel_admin):
        with patch("routes.hotel_admin_router._get_owned_hotel_id", new=AsyncMock(return_value=uuid.UUID("b1000000-0000-0000-0000-000000000001"))):
            with patch("routes.hotel_admin_router.RoomTypeRepository") as MockRoomRepo:
                mock_room_instance = MockRoomRepo.return_value
                mock_room_instance.get_by_id = AsyncMock(return_value=None)

                response = client_hotel_admin.post(
                    "/hotel-admin/inventory/bulk",
                    json={
                        "room_type_id": "c1000000-0000-0000-0000-000000000999",
                        "start_date": "2026-05-01",
                        "end_date": "2026-05-02",
                        "available_units": 8,
                        "price_per_night": "180.00",
                    },
                )

        assert response.status_code == 404
        assert "Habitación no encontrada" in response.json()["detail"]
