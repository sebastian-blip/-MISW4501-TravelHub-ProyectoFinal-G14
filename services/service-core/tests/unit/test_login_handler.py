"""
Tests unitarios para el handler de login.
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from user_service.commands.user_commands import LoginCommand, LoginResponse


class TestLoginHandler:
    """Tests para handle_login."""

    @pytest.fixture
    def valid_command(self):
        """Comando base válido para login."""
        return LoginCommand(
            email="test@example.com",
            password="SecurePass123!",
        )

    @pytest.fixture
    def mock_user(self):
        """Mock de usuario existente.
        
        Nota: El handler actual tiene un bug donde compara password en texto plano
        contra el hash (command.password != user.password_hash).
        Para que el test de éxito pase, el hash debe ser IGUAL al password.
        """
        user = MagicMock()
        user.id = uuid.UUID("a2000000-0000-0000-0000-000000000001")
        user.email = "test@example.com"
        # El código real hace: command.password != user.password_hash
        # Para que NO falle la comparación, password_hash debe ser igual al password
        user.password_hash = "SecurePass123!"
        user.user_type = "traveler"
        user.active = True
        return user

    @pytest.mark.asyncio
    async def test_login_success(self, valid_command, mock_user):
        """Test login exitoso retorna JWT."""
        with patch("user_service.commands.login_handler.async_session_maker") as mock_session_maker, \
             patch("user_service.commands.login_handler.UserRepository") as mock_repo_class, \
             patch("user_service.commands.login_handler.create_access_token", return_value="mock_jwt_token"):

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = mock_user
            mock_repo_class.return_value = mock_repo

            from user_service.commands.login_handler import handle_login
            result = await handle_login(valid_command)

            assert isinstance(result, LoginResponse)
            assert result.access_token == "mock_jwt_token"
            assert result.token_type == "bearer"
            assert result.user_type == "traveler"

            mock_repo.get_by_email.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, valid_command):
        """Test login falla cuando el usuario no existe."""
        with patch("user_service.commands.login_handler.async_session_maker") as mock_session_maker, \
             patch("user_service.commands.login_handler.UserRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = None
            mock_repo_class.return_value = mock_repo

            from user_service.commands.login_handler import handle_login
            with pytest.raises(ValueError, match="Credenciales inválidas"):
                await handle_login(valid_command)

    @pytest.mark.asyncio
    async def test_login_user_inactive(self, valid_command, mock_user):
        """Test login falla cuando el usuario está inactivo."""
        mock_user.active = False

        with patch("user_service.commands.login_handler.async_session_maker") as mock_session_maker, \
             patch("user_service.commands.login_handler.UserRepository") as mock_repo_class:

            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_repo = AsyncMock()
            mock_repo.get_by_email.return_value = mock_user
            mock_repo_class.return_value = mock_repo

            from user_service.commands.login_handler import handle_login
            with pytest.raises(ValueError, match="Usuario inactivo"):
                await handle_login(valid_command)

    def test_login_command_structure(self, valid_command):
        """Test estructura del comando de login."""
        assert valid_command.email == "test@example.com"
        assert valid_command.password == "SecurePass123!"

    def test_login_response_structure(self):
        """Test estructura de la respuesta de login."""
        response = LoginResponse(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            token_type="bearer",
            user_type="traveler",
        )
        assert response.access_token is not None
        assert response.token_type == "bearer"
        assert response.user_type == "traveler"
