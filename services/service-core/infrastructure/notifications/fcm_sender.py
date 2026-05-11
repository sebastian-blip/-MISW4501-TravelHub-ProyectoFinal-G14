"""FCM (Firebase Cloud Messaging) sender vía Firebase Admin SDK.

Diseño:

- **Init perezosa**: la primera llamada a `send_to_tokens` intenta inicializar
  Firebase Admin con el JSON del service account. Si falta la env var o el
  archivo no existe, marca la inicialización como fallida y todas las
  llamadas siguientes son no-op. Esto permite correr service-core en local
  o tests sin Firebase configurado — el reservation flow no falla por falta
  de push.
- **No-op tolerante**: si Firebase no está listo o un envío individual falla,
  devolvemos el count de éxitos sin levantar. El push es nice-to-have; la
  reserva NO debe abortarse porque un token esté caducado.
- **Threadsafe**: la flag `_initialized` se setea una sola vez; el SDK
  internamente sincroniza la app default global.

Variables de entorno (probadas en orden — se usa la primera que exista):

    FIREBASE_SERVICE_ACCOUNT_JSON — contenido del JSON inline. Recomendado en
        Kubernetes / contenedores: el secret se monta como env var sin tocar
        el filesystem.

    FIREBASE_SERVICE_ACCOUNT_PATH — path absoluto al JSON descargado de
        Firebase Console (Project Settings → Service accounts → Generate new
        private key). Útil en local dev.

Si ninguna está, el sender queda inactivo y todas las llamadas devuelven 0
sin levantar — la reserva nunca falla por falta de push.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from typing import Iterable, Optional

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    _HAS_FIREBASE = True
except ImportError:
    _HAS_FIREBASE = False
    firebase_admin = None  # type: ignore[assignment]
    credentials = None  # type: ignore[assignment]
    messaging = None  # type: ignore[assignment]


_init_lock = threading.Lock()
_init_attempted = False
_initialized = False


def _maybe_initialize() -> bool:
    global _init_attempted, _initialized
    with _init_lock:
        if _init_attempted:
            return _initialized
        _init_attempted = True

        if not _HAS_FIREBASE:
            logging.warning(
                "[FCM] firebase-admin no instalado; push notifications inactivas"
            )
            return False

        cred = _build_credential()
        if cred is None:
            return False

        try:
            firebase_admin.initialize_app(cred)
            _initialized = True
            logging.info("[FCM] Firebase Admin SDK inicializado")
            return True
        except Exception as e:  # pragma: no cover — depende del entorno real
            logging.error(f"[FCM] error inicializando Firebase Admin: {e}")
            return False


def _build_credential():
    """Construye la credencial probando primero el env var inline (modo K8s
    Secret) y después el path en disco (modo local dev). Devuelve `None` si
    ninguno está disponible — el sender queda inactivo."""
    inline = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if inline:
        try:
            payload = json.loads(inline)
            logging.info("[FCM] usando credencial desde FIREBASE_SERVICE_ACCOUNT_JSON (inline)")
            return credentials.Certificate(payload)
        except json.JSONDecodeError as e:
            logging.error(f"[FCM] FIREBASE_SERVICE_ACCOUNT_JSON no es JSON válido: {e}")
            return None
        except Exception as e:
            logging.error(f"[FCM] error parseando FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
            return None

    path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if path:
        if not os.path.exists(path):
            logging.warning(
                f"[FCM] FIREBASE_SERVICE_ACCOUNT_PATH apunta a un archivo que no "
                f"existe ({path!r}); push inactivas"
            )
            return None
        try:
            logging.info(f"[FCM] usando credencial desde {path}")
            return credentials.Certificate(path)
        except Exception as e:
            logging.error(f"[FCM] error leyendo credencial desde {path}: {e}")
            return None

    logging.warning(
        "[FCM] ni FIREBASE_SERVICE_ACCOUNT_JSON ni FIREBASE_SERVICE_ACCOUNT_PATH "
        "están configuradas; push inactivas"
    )
    return None


def send_to_tokens(
    tokens: Iterable[str],
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> int:
    """Envía una notificación FCM a cada token. Devuelve el número de envíos
    exitosos. Si Firebase no está configurado, devuelve 0 sin levantar."""
    if not _maybe_initialize():
        return 0

    payload_data = {str(k): str(v) for k, v in (data or {}).items()}
    sent = 0
    for token in tokens:
        token = (token or "").strip()
        if not token:
            continue
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=payload_data,
                token=token,
            )
            response = messaging.send(message)
            logging.info(f"[FCM] enviado {response} → {token[:12]}…")
            sent += 1
        except Exception as e:
            # Tokens caducados / desregistrados / 404 — no es fatal.
            logging.warning(f"[FCM] fallo enviando a {token[:12]}…: {e}")
    return sent
