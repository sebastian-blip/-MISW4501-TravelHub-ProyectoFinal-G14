"""
Tests unitarios para los handlers de consulta de usuarios.
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from user_service.queries.user_queries import (
    GetUserByIdQuery,
    GetUserByEmailQuery,
    GetUserProfileQuery,
    UserResponse,
    UserProfileResponse,
)


class TestGetUserByIdHandler:
    """Tests para GetUserByIdQueryHandler."""

    @pytest.fixture
    def mock_user(self):
        """Mock de usuario existente."""
        user = MagicMock()
        user.id = uuid.UUID("a2000000-0000-0000-0000-000000000001")
        user.email = "test@example.com"
        user.first_name = "Juan"
        user.last_name = "Pérez"
        user.phone = "+573001234567"
        user.country_id = uuid.UUID("a1000000-0000-0000-0000-000000000001")
        user.user_type = "traveler"
        user.email_verified = True
        user.mfa_enabled = False
        user.active = True
        return user

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, mock_user):
        """Test consulta por ID exitosa."""
        with patch("user_service.queries.get_user_handler.async_session_maker") as mock_session_maker, \
             patch("user_service.queries.get_user_handler.UserRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = mock_user
            mock_repo_class.return_value = mock_repo

            from user_service.queries.get_user_handler import GetUserByIdQueryHandler
            handler = GetUserByIdQueryHandler()
            query = GetUserByIdQuery(user_id=uuid.UUID("a2000000-0000-0000-0000-000000000001"))
            result = await handler.handle(query)

            assert isinstance(result, UserResponse)
            assert result.id == mock_user.id
            assert result.email == mock_user.email
            assert result.first_name == mock_user.first_name
            assert result.active is True

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self):
        """Test consulta por ID falla cuando no existe."""
        with patch("user_service.queries.get_user_handler.async_session_maker") as mock_session_maker, \
             patch("user_service.queries.get_user_handler.UserRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            from user_service.queries.get_user_handler import GetUserByIdQueryHandler
            handler = GetUserByIdQueryHandler()
            query = GetUserByIdQuery(user_id=uuid.UUID("a2000000-0000-0000-0000-000000000001"))

            with pytest.raises(ValueError, match="no encontrado"):
                await handler.handle(query)


class TestGetUserByEmailHandler:
    """Tests para GetUserByEmailQueryHandler."""

    @pytest.fixture
    def mock_user(self):
        """Mock de usuario existente."""
        user = MagicMock()
        user.id = uuid.UUID("a2000000-0000-0000-0000-000000000001")
        user.email = "test@example.com"
        user.first_name = "Juan"
        user.last_name = "Pérez"
        user.phone = "+573001234567"
        user.country_id = uuid.UUID("a1000000-0000-0000-0000-000000000001")
        user.user_type = "traveler"
        user.email_verified = True
        user.mfa_enabled = False
        user.active = True
        return user

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, mock_user):
        """Test consulta por email exitosa."""
        with patch("user_service.queries.get_user_handler.async_session_maker") as mock_session_maker, \
             patch("user_service.queries.get_user_handler.UserRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = mock_user
            mock_repo_class.return_value = mock_repo

            from user_service.queries.get_user_handler import GetUserByEmailQueryHandler
            handler = GetUserByEmailQueryHandler()
            query = GetUserByEmailQuery(email="test@example.com")
            result = await handler.handle(query)

            assert isinstance(result, UserResponse)
            assert result.id == mock_user.id
            assert result.email == mock_user.email
            assert result.first_name == mock_user.first_name

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self):
        """Test consulta por email falla cuando no existe."""
        with patch("user_service.queries.get_user_handler.async_session_maker") as mock_session_maker, \
             patch("user_service.queries.get_user_handler.UserRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = None
            mock_repo_class.return_value = mock_repo

            from user_service.queries.get_user_handler import GetUserByEmailQueryHandler
            handler = GetUserByEmailQueryHandler()
            query = GetUserByEmailQuery(email="notfound@example.com")

            with pytest.raises(ValueError, match="no encontrado"):
                await handler.handle(query)


class TestUserResponse:
    """Tests para UserResponse."""

    def test_user_response_from_orm(self):
        """Test conversión desde ORM."""
        user = MagicMock()
        user.id = uuid.UUID("a2000000-0000-0000-0000-000000000001")
        user.email = "test@example.com"
        user.first_name = "Juan"
        user.last_name = "Pérez"
        user.phone = "+573001234567"
        user.country_id = uuid.UUID("a1000000-0000-0000-0000-000000000001")
        user.user_type = "traveler"
        user.email_verified = True
        user.mfa_enabled = False
        user.active = True

        response = UserResponse.from_orm(user)

        assert response.id == user.id
        assert response.email == user.email
        assert response.first_name == user.first_name
        assert response.last_name == user.last_name
        assert response.phone == user.phone
        assert response.country_id == user.country_id
        assert response.user_type == user.user_type
        assert response.email_verified is True
        assert response.mfa_enabled is False
        assert response.active is True

    def test_user_response_structure(self):
        """Test estructura de UserResponse."""
        response = UserResponse(
            id=uuid.UUID("a2000000-0000-0000-0000-000000000001"),
            email="test@example.com",
            first_name="Juan",
            last_name="Pérez",
            phone=None,
            country_id=None,
            user_type="traveler",
            email_verified=False,
            mfa_enabled=False,
            active=True,
        )
        assert response.phone is None
        assert response.country_id is None


class TestGetUserProfileHandler:
    """Tests para GetUserProfileQueryHandler."""

    @pytest.fixture
    def mock_user(self):
        """Mock de usuario existente."""
        user = MagicMock()
        user.id = uuid.UUID("a2000000-0000-0000-0000-000000000001")
        user.email = "test@example.com"
        user.first_name = "Juan"
        user.last_name = "Pérez"
        user.phone = "+573001234567"
        user.country_id = uuid.UUID("a1000000-0000-0000-0000-000000000001")
        user.user_type = "traveler"
        user.email_verified = True
        user.mfa_enabled = False
        user.active = True
        return user

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, mock_user):
        """Test consulta de perfil exitosa con conteos."""
        with patch("user_service.queries.get_user_handler.async_session_maker") as mock_session_maker, \
             patch("user_service.queries.get_user_handler.UserRepository") as mock_user_repo_class, \
             patch("user_service.queries.get_user_handler.ReservationRepository") as mock_reservation_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = mock_user
            mock_user_repo_class.return_value = mock_user_repo

            mock_reservation_repo = AsyncMock()
            mock_reservation_repo.count_past_by_user.return_value = 5
            mock_reservation_repo.count_pending_by_user.return_value = 2
            mock_reservation_repo_class.return_value = mock_reservation_repo

            from user_service.queries.get_user_handler import GetUserProfileQueryHandler
            handler = GetUserProfileQueryHandler()
            query = GetUserProfileQuery(user_id=uuid.UUID("a2000000-0000-0000-0000-000000000001"))
            result = await handler.handle(query)

            assert isinstance(result, UserProfileResponse)
            assert result.id == mock_user.id
            assert result.email == mock_user.email
            assert result.past_reservations_count == 5
            assert result.pending_reservations_count == 2

    @pytest.mark.asyncio
    async def test_get_user_profile_not_found(self):
        """Test consulta de perfil falla cuando no existe."""
        with patch("user_service.queries.get_user_handler.async_session_maker") as mock_session_maker, \
             patch("user_service.queries.get_user_handler.UserRepository") as mock_user_repo_class, \
             patch("user_service.queries.get_user_handler.ReservationRepository") as mock_reservation_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_user_repo = AsyncMock()
            mock_user_repo.get_by_id.return_value = None
            mock_user_repo_class.return_value = mock_user_repo

            mock_reservation_repo = AsyncMock()
            mock_reservation_repo_class.return_value = mock_reservation_repo

            from user_service.queries.get_user_handler import GetUserProfileQueryHandler
            handler = GetUserProfileQueryHandler()
            query = GetUserProfileQuery(user_id=uuid.UUID("a2000000-0000-0000-0000-000000000001"))

            with pytest.raises(ValueError, match="no encontrado"):
                await handler.handle(query)
