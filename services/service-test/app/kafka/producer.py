import json
import logging
import os
import ssl
from aiokafka import AIOKafkaProducer

TOPIC_REQUESTS = "user-validation-requests"

_producer: AIOKafkaProducer | None = None


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
        
        resolved_ca_path = _resolve_ca_path(ca_path)
        
        if resolved_ca_path and os.path.isfile(resolved_ca_path):
            try:
                ssl_context = ssl.create_default_context(cafile=resolved_ca_path)
                config["ssl_context"] = ssl_context
                logging.info(f"[service-test Producer] Usando SASL/SSL con certificado: {resolved_ca_path}")
            except Exception as e:
                logging.error(f"[service-test Producer] Error cargando certificado: {e}")
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                config["ssl_context"] = ssl_context
        else:
            logging.warning(f"[service-test Producer] Certificado no encontrado, usando SSL sin verificación")
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            config["ssl_context"] = ssl_context
    
    _producer = AIOKafkaProducer(**config)
    await _producer.start()
    logging.info(f"[Producer] conectado a Kafka en {bootstrap_servers}")


async def stop_producer():
    global _producer
    if _producer:
        await _producer.stop()


async def publish_user_check(email: str):
    if _producer is None:
        raise RuntimeError("Producer no inicializado")

    payload = json.dumps({"email": email}).encode("utf-8")
    await _producer.send_and_wait(TOPIC_REQUESTS, payload)
    logging.info(f"[Producer] evento publicado → topic={TOPIC_REQUESTS} email={email}")
