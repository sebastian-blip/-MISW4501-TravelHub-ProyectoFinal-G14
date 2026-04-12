import json
import asyncio
from aiokafka import AIOKafkaProducer
from typing import Any

from hotel_service.events.publisher import EventPublisherABC, DEFAULT_TOPIC


class KafkaPublisher(EventPublisherABC):
    def __init__(self, bootstrap_servers: str = "travelhub_kafka:9092"):
        self._bootstrap = bootstrap_servers
        self._producer: AIOKafkaProducer | None = None

    async def _ensure(self):
        if self._producer is None:
            self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap)
            await self._producer.start()

    async def publish(self, event: Any) -> None:
        await self._ensure()
        payload = json.dumps(event.to_dict()).encode("utf-8")
        topic = getattr(event, "topic", DEFAULT_TOPIC)
        # send and wait for completion
        await self._producer.send_and_wait(topic, payload)

    async def stop(self):
        if self._producer is not None:
            await self._producer.stop()
