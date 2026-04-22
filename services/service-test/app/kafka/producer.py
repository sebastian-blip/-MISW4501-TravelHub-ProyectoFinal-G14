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
    global _producer

    kafka_local = os.getenv("KAFKA_LOCAL", "false").lower() == "true"

    config = {
        "bootstrap_servers": bootstrap_servers,
    }

    if not kafka_local:
        config["sasl_mechanism"] = "SCRAM-SHA-256"
        config["security_protocol"] = "SASL_PLAINTEXT"  # AWS MSK usa SSL
        config["sasl_plain_username"] = os.getenv("KAFKA_USERNAME")
        config["sasl_plain_password"] = os.getenv("KAFKA_PASSWORD")
    else:
        config["sasl_mechanism"] = "PLAIN"



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
