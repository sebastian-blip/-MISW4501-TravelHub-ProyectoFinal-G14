import asyncio
import json
import logging
import os
import ssl
from aiokafka import AIOKafkaConsumer

TOPIC_RESULTS = "user-validation-results"
TOPIC_RESERVATION_RESULTS = "reservation-validate-results"

# Futures pendientes por correlation_id — el handler espera aquí
_pending: dict[str, asyncio.Future] = {}

_consumer: AIOKafkaConsumer | None = None
_task: asyncio.Task | None = None


def _resolve_ca_path(ca_path: str) -> str | None:
    """Resuelve la ruta del certificado CA, buscando alternativas si no existe."""
    if not ca_path:
        return None
    
    if os.path.isfile(ca_path):
        return ca_path
    
    alternatives = [
        "/service/ca-cert.pem",
        "/app/certs/ca-cert.pem",
        "/certs/ca-cert.pem",
        "./certs/ca-cert.pem",
    ]
    
    for alt in alternatives:
        if os.path.isfile(alt):
            logging.info(f"[Kafka] Usando certificado alternativo: {alt}")
            return alt
    
    if ca_path.startswith("./") or ca_path.startswith("../"):
        abs_path = os.path.abspath(ca_path)
        if os.path.isfile(abs_path):
            return abs_path
    
    logging.warning(f"[Kafka] No se encontró certificado CA en: {ca_path}")
    return None


async def start_reply_consumer(
    bootstrap_servers: str,
    use_ssl: bool = False,
    username: str = "",
    password: str = "",
    ca_path: str = ""
):
    """Inicia el consumidor de respuestas con soporte para SASL/SSL en AWS."""
    global _consumer, _task
    
    config = {
        "bootstrap_servers": bootstrap_servers,
        "group_id": "service-core-reply-group",
        "auto_offset_reset": "latest",
        "enable_auto_commit": True,
    }
    
    # Configuración SASL/SSL para AWS
    if use_ssl and username and password:
        config["security_protocol"] = "SASL_SSL"
        config["sasl_mechanism"] = "PLAIN"
        config["sasl_plain_username"] = username
        config["sasl_plain_password"] = password
        
        resolved_ca_path = _resolve_ca_path(ca_path)
        
        if resolved_ca_path and os.path.isfile(resolved_ca_path):
            try:
                ssl_context = ssl.create_default_context(cafile=resolved_ca_path)
                config["ssl_context"] = ssl_context
                logging.info(f"[service-core ReplyConsumer] Usando SASL/SSL con certificado: {resolved_ca_path}")
            except Exception as e:
                logging.error(f"[service-core ReplyConsumer] Error cargando certificado: {e}")
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                config["ssl_context"] = ssl_context
        else:
            logging.warning(f"[service-core ReplyConsumer] Certificado no encontrado, usando SSL sin verificación")
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            config["ssl_context"] = ssl_context
    
    _consumer = AIOKafkaConsumer(
        TOPIC_RESULTS,
        TOPIC_RESERVATION_RESULTS,
        **config
    )
    await _consumer.start()
    _task = asyncio.create_task(_consume())
    logging.info(f"[service-core ReplyConsumer] escuchando topics={TOPIC_RESULTS}, {TOPIC_RESERVATION_RESULTS}")


async def stop_reply_consumer():
    global _consumer, _task
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    if _consumer:
        await _consumer.stop()


async def wait_for_reply(correlation_id: str, timeout: float = 5.0) -> dict:
    """Bloquea hasta recibir la respuesta con el correlation_id dado."""
    loop = asyncio.get_event_loop()
    future: asyncio.Future = loop.create_future()
    _pending[correlation_id] = future
    try:
        return await asyncio.wait_for(asyncio.shield(future), timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Sin respuesta de Kafka para correlation_id={correlation_id}")
    finally:
        _pending.pop(correlation_id, None)


async def _consume():
    try:
        async for msg in _consumer:
            payload = json.loads(msg.value.decode("utf-8"))
            correlation_id = payload.get("correlation_id", "")
            future = _pending.get(correlation_id)
            if future and not future.done():
                future.set_result(payload)
                logging.info(f"[service-core ReplyConsumer] respuesta recibida → correlation_id={correlation_id}, topic={msg.topic}")
    except asyncio.CancelledError:
        pass
