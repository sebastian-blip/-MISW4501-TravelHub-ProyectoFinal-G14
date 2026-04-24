import pytest

@pytest.fixture
def dashboard_client():
    """Fixture para endpoints del dashboard (usa toda la app principal)."""
    from main import app
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture
def notification_client(monkeypatch):
    """Fixture para aislar router de notificación (evita conflicto de imports/settings)"""
    # Setea las env vars aquí, antes del import
    monkeypatch.setenv("RESEND_API_KEY", "fake-api-key")
    monkeypatch.setenv("TOKEN_SOPORT_SERVICES", "mi-token-secreto")
    # Importa aquí adentro la app mínima
    from fastapi import FastAPI
    from routers.notification_router import router
    from fastapi.testclient import TestClient
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_send_email_notification(monkeypatch):
    """Mock para evitar envío real de correo, usado automáticamente si email_handler se importa."""
    from notification_service import email_handler
    def fake_send_email_notification(email, message):
        return True
    monkeypatch.setattr(email_handler, "send_email_notification", fake_send_email_notification)