"""
Tests unitarios para el handler de registro de usuarios.
"""
import uuid
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from user_service.commands.user_commands import RegisterUserCommand, RegisterUserResponse


class TestRegisterUserHandler:
    """Tests para handle_register_user."""

    @pytest.fixture
    def valid_command(self):
        """Comando base válido para registro."""
        return RegisterUserCommand(
            email="test@example.com",
            password="SecurePass123!",
            first_name="Juan",
            last_name="Pérez",
            user_type="traveler",
            phone="+573001234567",
            country_id=uuid.UUID("a1000000-0000-0000-0000-000000000001"),
        )

    @pytest.fixture
    def mock_user(self):
        """Mock de usuario creado."""
        user = MagicMock()
        user.id = uuid.UUID("a2000000-0000-0000-0000-000000000001")
        user.email = "test@example.com"
        user.first_name = "Juan"
        user.last_name = "Pérez"
        user.user_type = "traveler"
        return user

    @pytest.mark.asyncio
    async def test_register_user_success(self, valid_command, mock_user):
        """Test registro exitoso de usuario."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "sent"}

        with patch("user_service.commands.register_user_handler.async_session_maker") as mock_session_maker, \
             patch("user_service.commands.register_user_handler.UserRepository") as mock_repo_class, \
             patch("user_service.commands.register_user_handler.hash_password", return_value="hashed_password"), \
             patch("httpx.AsyncClient") as mock_http_client:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.email_exists.return_value = False
            mock_repo.create.return_value = mock_user
            mock_repo_class.return_value = mock_repo

            mock_http_instance = AsyncMock()
            mock_http_instance.post = AsyncMock(return_value=mock_response)
            mock_http_client.return_value.__aenter__ = AsyncMock(return_value=mock_http_instance)
            mock_http_client.return_value.__aexit__ = AsyncMock(return_value=False)

            from user_service.commands.register_user_handler import handle_register_user
            result = await handle_register_user(valid_command)

            assert isinstance(result, RegisterUserResponse)
            assert result.id == mock_user.id
            assert result.email == mock_user.email
            assert result.first_name == mock_user.first_name
            assert result.last_name == mock_user.last_name
            assert result.user_type == mock_user.user_type

            mock_repo.email_exists.assert_called_once_with("test@example.com")
            mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_invalid_type(self, valid_command):
        """Test registro falla con user_type inválido."""
        invalid_command = RegisterUserCommand(
            email="test@example.com",
            password="SecurePass123!",
            first_name="Juan",
            last_name="Pérez",
            user_type="invalid_type",
        )

        from user_service.commands.register_user_handler import handle_register_user
        with pytest.raises(ValueError, match="user_type inválido"):
            await handle_register_user(invalid_command)

    @pytest.mark.asyncio
    async def test_register_user_email_already_exists(self, valid_command, mock_user):
        """Test registro falla cuando el email ya existe."""
        with patch("user_service.commands.register_user_handler.async_session_maker") as mock_session_maker, \
             patch("user_service.commands.register_user_handler.UserRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.email_exists.return_value = True
            mock_repo_class.return_value = mock_repo

            from user_service.commands.register_user_handler import handle_register_user
            with pytest.raises(ValueError, match="ya est registrado"):
                await handle_register_user(valid_command)

    def test_valid_user_types(self):
        """Test que los tipos de usuario válidos están definidos correctamente."""
        from user_service.repository.user_repository import VALID_USER_TYPES
        expected = {"traveler", "hotel_admin", "agency", "admin"}
        assert VALID_USER_TYPES == expected

    def test_register_command_structure(self, valid_command):
        """Test estructura del comando de registro."""
        assert valid_command.email == "test@example.com"
        assert valid_command.first_name == "Juan"
        assert valid_command.last_name == "Pérez"
        assert valid_command.user_type == "traveler"
        assert valid_command.phone == "+573001234567"
        assert valid_command.country_id == uuid.UUID("a1000000-0000-0000-0000-000000000001")

    def test_register_response_structure(self, mock_user):
        """Test estructura de la respuesta de registro."""
        response = RegisterUserResponse(
            id=mock_user.id,
            email=mock_user.email,
            first_name=mock_user.first_name,
            last_name=mock_user.last_name,
            user_type=mock_user.user_type,
        )
        assert response.id == uuid.UUID("a2000000-0000-0000-0000-000000000001")
        assert response.email == "test@example.com"
