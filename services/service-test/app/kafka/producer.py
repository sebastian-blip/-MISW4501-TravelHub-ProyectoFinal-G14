import json
import logging
import os
from aiokafka import AIOKafkaProducer

TOPIC_REQUESTS = "user-validation-requests"

_producer: AIOKafkaProducer | None = None


async def start_producer(
    bootstrap_servers: str,
    use_ssl: bool = False,
    username: str = "",
    password: str = ""
):
    """Inicia el productor de Kafka con soporte para SASL."""
    global _producer
    
    config = {
        "bootstrap_servers": bootstrap_servers,
    }
    
    # Configuración SASL para AWS
    if use_ssl and username and password:
        config["sasl_mechanism"] = "SCRAM-SHA-256"
        config["security_protocol"] = "SASL_PLAINTEXT"
        config["sasl_plain_username"] = username
        config["sasl_plain_password"] = password
    
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
