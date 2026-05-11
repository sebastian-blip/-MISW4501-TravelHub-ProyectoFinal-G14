"""Tests del router `/users/me/device-tokens`. Mockean el repositorio para
no necesitar BD real — el contrato testeado es la traducción HTTP/JSON +
validaciones del payload + propagación del `user_id` desde el JWT.
"""
import uuid
import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.device_token_router import router as device_token_router
from user_service.utils.security import get_current_user


VALID_USER_ID = "a2000000-0000-0000-0000-000000000001"


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(device_token_router)
    app.dependency_overrides[get_current_user] = lambda: {"user_id": VALID_USER_ID}
    # `get_session` se reemplaza con un None: las rutas pasan el session al
    # repo, pero el repo está mockeado a nivel de método.
    from infrastructure.database import get_session
    app.dependency_overrides[get_session] = lambda: None
    return TestClient(app)


def _fake_record(token: str = "fcm-abc"):
    """DeviceToken-shaped object para que el response_model pueda construirse."""
    now = datetime.datetime(2026, 5, 4, 12, 0, 0, tzinfo=datetime.timezone.utc)

    class _Record:
        pass

    record = _Record()
    record.id = uuid.UUID("d1000000-0000-0000-0000-000000000001")
    record.user_id = uuid.UUID(VALID_USER_ID)
    record.token = token
    record.platform = "android"
    record.app_version = "0.1.1"
    record.last_seen_at = now
    record.created_at = now
    return record


class TestRegisterDeviceToken:
    def test_upserts_token_and_returns_201(self, client):
        with patch(
            "routes.device_token_router.DeviceTokenRepository.upsert",
            new=AsyncMock(return_value=_fake_record()),
        ):
            response = client.post(
                "/users/me/device-tokens",
                json={
                    "token": "fcm-abc",
                    "platform": "android",
                    "app_version": "0.1.1",
                },
            )

        assert response.status_code == 201
        body = response.json()
        assert body["user_id"] == VALID_USER_ID
        assert body["platform"] == "android"
        assert body["app_version"] == "0.1.1"
        assert body["last_seen_at"].startswith("2026-05-04T12:00:00")

    def test_rejects_unknown_platform(self, client):
        response = client.post(
            "/users/me/device-tokens",
            json={"token": "fcm-abc", "platform": "windows-phone"},
        )
        assert response.status_code == 400
        assert "platform" in response.json()["detail"]

    def test_rejects_blank_token(self, client):
        response = client.post(
            "/users/me/device-tokens",
            json={"token": "   ", "platform": "android"},
        )
        assert response.status_code == 400

    def test_app_version_is_optional(self, client):
        with patch(
            "routes.device_token_router.DeviceTokenRepository.upsert",
            new=AsyncMock(return_value=_fake_record()),
        ) as upsert_mock:
            response = client.post(
                "/users/me/device-tokens",
                json={"token": "fcm-abc", "platform": "android"},
            )
        assert response.status_code == 201
        # El repo recibe app_version=None cuando el cliente no lo envía.
        kwargs = upsert_mock.call_args.kwargs
        assert kwargs["app_version"] is None

    def test_trims_token_before_persisting(self, client):
        with patch(
            "routes.device_token_router.DeviceTokenRepository.upsert",
            new=AsyncMock(return_value=_fake_record()),
        ) as upsert_mock:
            response = client.post(
                "/users/me/device-tokens",
                json={"token": "  fcm-abc  ", "platform": "android"},
            )
        assert response.status_code == 201
        assert upsert_mock.call_args.kwargs["token"] == "fcm-abc"


class TestDeleteDeviceToken:
    def test_deletes_existing_token_204(self, client):
        with patch(
            "routes.device_token_router.DeviceTokenRepository.delete",
            new=AsyncMock(return_value=True),
        ):
            response = client.request(
                "DELETE",
                "/users/me/device-tokens",
                json={"token": "fcm-abc"},
            )
        assert response.status_code == 204
        assert response.text == ""

    def test_idempotent_when_token_unknown(self, client):
        # Repo devuelve False (no había nada que borrar) y aun así el
        # endpoint responde 204 — semantica idempotente.
        with patch(
            "routes.device_token_router.DeviceTokenRepository.delete",
            new=AsyncMock(return_value=False),
        ):
            response = client.request(
                "DELETE",
                "/users/me/device-tokens",
                json={"token": "fcm-unknown"},
            )
        assert response.status_code == 204
