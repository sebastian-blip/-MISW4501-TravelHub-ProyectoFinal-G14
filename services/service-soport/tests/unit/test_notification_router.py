import pytest

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "fake-api-key")
    monkeypatch.setenv("TOKEN_SOPORT_SERVICES", "mi-token-secreto")

@pytest.fixture
def client():
    # Importar AQUI después de setear env vars
    from fastapi import FastAPI
    from routers.notification_router import router
    app = FastAPI()
    app.include_router(router)
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_send_email_notification(monkeypatch):
    # Importar adentro del fixture para que no lea viejo env
    from notification_service import email_handler
    def fake_send_email_notification(email, message):
        return True
    monkeypatch.setattr(email_handler, "send_email_notification", fake_send_email_notification)

def test_send_email_ok(client):
    headers = {"Authorization": "Bearer mi-token-secreto"}
    data = {"email": "test@mail.com", "message": "Hola"}
    response = client.post("/notification/send-email", json=data, headers=headers)
    assert response.status_code == 201

def test_send_email_missing_token(client):
    data = {"email": "test@mail.com", "message": "Hola"}
    response = client.post("/notification/send-email", json=data)
    assert response.status_code == 401

def test_send_email_wrong_token(client):
    headers = {"Authorization": "Bearer token-incorrecto"}
    data = {"email": "test@mail.com", "message": "Hola"}
    response = client.post("/notification/send-email", json=data, headers=headers)
    assert response.status_code == 401