import asyncio
import json
import time
import logging
import os
from typing import List

from aiokafka import AIOKafkaConsumer

from hotel_service.events.reservation_events import ReservationCreatedEvent
from hotel_service.availability.repository import HotelAvailabilityRepository
from hotel_service.metrics import reservations_consumed_total, reservation_consistency_lag_seconds


DEFAULT_KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "travelhub_kafka:9092")
DEFAULT_AVAILABILITY_CONSUMER_COUNT = int(os.getenv("AVAILABILITY_CONSUMER_COUNT", "4"))


class AvailabilityReadModelConsumer:
    def __init__(
        self,
        bootstrap_servers: str = DEFAULT_KAFKA_BOOTSTRAP_SERVERS,
        topic: str = "reservation-created",
        group_id: str = "hotel-availability-readmodel",
        consumer_count: int = DEFAULT_AVAILABILITY_CONSUMER_COUNT,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.consumer_count = max(1, consumer_count)
        self._consumers: List[AIOKafkaConsumer] = []
        self._tasks: List[asyncio.Task] = []
        self._running = False
        self.repository = HotelAvailabilityRepository()

    async def start(self):
        await self.repository.seed_from_rooms()
        self._running = True
        for worker_index in range(self.consumer_count):
            consumer = AIOKafkaConsumer(
                self.topic,
                group_id=self.group_id,
                bootstrap_servers=self.bootstrap_servers,
                client_id=f"availability-consumer-{worker_index}",
                enable_auto_commit=True,
                auto_offset_reset="earliest",
            )
            await consumer.start()
            self._consumers.append(consumer)
            task = asyncio.create_task(self._consume(consumer))
            self._tasks.append(task)

    async def stop(self):
        self._running = False
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        for consumer in self._consumers:
            await consumer.stop()
        self._tasks.clear()
        self._consumers.clear()

    async def _consume(self, consumer: AIOKafkaConsumer):
        try:
            async for msg in consumer:
                payload = json.loads(msg.value.decode("utf-8"))
                await self._handle(payload)
                if not self._running:
                    break
        except asyncio.CancelledError:
            pass

    async def _handle(self, payload: dict):
        event = ReservationCreatedEvent.from_dict(payload)
        reservations_consumed_total.inc()
        if event.created_at and hasattr(event.created_at, "timestamp"):
            lag = time.time() - event.created_at.timestamp()
            reservation_consistency_lag_seconds.observe(lag)
        await self.repository.upsert(
            hotel_id=event.hotel_id,
            room_id=event.room_id,
            hotel_name=event.hotel_name or "",
            city=event.city or "",
            available=False,
            room_type=event.room_type,
            price_per_night=event.price_per_night,
        )
