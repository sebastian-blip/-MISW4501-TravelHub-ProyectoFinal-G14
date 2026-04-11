import json
import logging
import os
import ssl
from aiokafka import AIOKafkaProducer

TOPIC_REQUESTS = "user-validation-requests"
TOPIC_STEP_EVENTS = "step-change-events"
TOPIC_RESERVATION_VALIDATE = "reservation-validate-requests"
TOPIC_AWS_TEST = "aws-test-messages"

_producer: AIOKafkaProducer | None = None


def _resolve_ca_path(ca_path: str) -> str | None:
    """Resuelve la ruta del certificado CA, buscando alternativas si no existe."""
    if not ca_path:
        return None
    
    # Si existe la ruta especificada, usarla
    if os.path.isfile(ca_path):
        return ca_path
    
    # Buscar alternativas comunes
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
    
    # Si no se encuentra, verificar si es una ruta relativa y convertirla
    if ca_path.startswith("./") or ca_path.startswith("../"):
        abs_path = os.path.abspath(ca_path)
        if os.path.isfile(abs_path):
            return abs_path
    
    logging.warning(f"[Kafka] No se encontró certificado CA en: {ca_path}")
    return None


async def start_producer(
    bootstrap_servers: str,
    use_ssl: bool = False,
    username: str = "",
    password: str = "",
    ca_path: str = ""
):
    """Inicia el productor de Kafka con soporte para SASL/SSL en AWS."""
    global _producer
    
    config = {
        "bootstrap_servers": bootstrap_servers,
    }
    
    # Configuración SASL/SSL para AWS
    if use_ssl and username and password:
        config["security_protocol"] = "SASL_SSL"
        config["sasl_mechanism"] = "PLAIN"
        config["sasl_plain_username"] = username
        config["sasl_plain_password"] = password
        
        # Resolver ruta del certificado
        resolved_ca_path = _resolve_ca_path(ca_path)
        
        if resolved_ca_path and os.path.isfile(resolved_ca_path):
            try:
                ssl_context = ssl.create_default_context(cafile=resolved_ca_path)
                config["ssl_context"] = ssl_context
                logging.info(f"[service-core Producer] Usando SASL/SSL con certificado: {resolved_ca_path}")
            except Exception as e:
                logging.error(f"[service-core Producer] Error cargando certificado {resolved_ca_path}: {e}")
                logging.warning(f"[service-core Producer] Continuando sin verificación de certificado (inseguro)")
                # Intentar con SSL sin verificación de CA (solo para pruebas)
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                config["ssl_context"] = ssl_context
        else:
            logging.warning(f"[service-core Producer] Certificado no encontrado en '{ca_path}', usando SSL sin verificación de CA")
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            config["ssl_context"] = ssl_context
    
    _producer = AIOKafkaProducer(**config)
    await _producer.start()
    logging.info(f"[service-core Producer] conectado a Kafka en {bootstrap_servers}")


async def stop_producer():
    global _producer
    if _producer:
        await _producer.stop()


async def publish_user_check(email: str, correlation_id: str):
    if _producer is None:
        raise RuntimeError("Kafka producer no inicializado")

    payload = json.dumps({"email": email, "correlation_id": correlation_id}).encode("utf-8")
    await _producer.send_and_wait(TOPIC_REQUESTS, payload)
    logging.info(f"[service-core Producer] pregunta enviada → email={email} correlation_id={correlation_id}")


async def publish_step_change(task_id: int, previous_step: int, new_step: int, history: list):
    """Publica un evento cuando cambia el paso de una tarea."""
    if _producer is None:
        raise RuntimeError("Kafka producer no inicializado")
    
    payload = json.dumps({
        "event": "step_changed",
        "task_id": task_id,
        "previous_step": previous_step,
        "new_step": new_step,
        "history": history,
        "action_required": "query_users"
    }).encode("utf-8")
    
    await _producer.send_and_wait(TOPIC_STEP_EVENTS, payload)
    logging.info(f"[service-core Producer] evento de paso enviado → task_id={task_id}, step={new_step}")


async def publish_reservation_validate(
    user_id: str,
    hotel_id: str,
    room_type_id: str,
    check_in: str,
    check_out: str,
    correlation_id: str
):
    """
    Publica evento para validar si una reserva existe.
    service-test debe responder con exists: true/false.
    """
    if _producer is None:
        raise RuntimeError("Kafka producer no inicializado")
    
    payload = json.dumps({
        "event": "reservation_validate_request",
        "user_id": user_id,
        "hotel_id": hotel_id,
        "room_type_id": room_type_id,
        "check_in": check_in,
        "check_out": check_out,
        "correlation_id": correlation_id
    }).encode("utf-8")
    
    await _producer.send_and_wait(TOPIC_RESERVATION_VALIDATE, payload)
    logging.info(f"[service-core Producer] validación reserva enviada → correlation_id={correlation_id}")


async def publish_test_message(
    message: str,
    correlation_id: str,
    priority: str = "normal",
    metadata: dict = None,
    timestamp: str = None
):
    """
    Publica un mensaje de prueba para validar conectividad en AWS.
    service-test recibirá este mensaje y responderá.
    """
    if _producer is None:
        raise RuntimeError("Kafka producer no inicializado")
    
    import socket
    hostname = socket.gethostname()
    
    payload = json.dumps({
        "event": "aws_test_message",
        "message": message,
        "correlation_id": correlation_id,
        "priority": priority,
        "metadata": metadata or {},
        "timestamp": timestamp,
        "source": {
            "service": "service-core",
            "host": hostname,
            "port": 8000
        }
    }).encode("utf-8")
    
    await _producer.send_and_wait(TOPIC_AWS_TEST, payload)
    logging.info(f"[service-core Producer] mensaje de prueba AWS enviado → correlation_id={correlation_id}, priority={priority}")
