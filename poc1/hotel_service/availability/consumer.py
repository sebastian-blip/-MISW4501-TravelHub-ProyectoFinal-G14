import asyncio
import json
import time
import logging
from typing import Optional

from aiokafka import AIOKafkaConsumer
import time
import logging

from hotel_service.events.reservation_events import ReservationCreatedEvent
from hotel_service.availability.repository import HotelAvailabilityRepository
from hotel_service.metrics import reservations_consumed_total, reservation_consistency_lag_seconds


class AvailabilityReadModelConsumer:
    def __init__(self, bootstrap_servers: str = "travelhub_kafka:9092", topic: str = "reservation-created", group_id: str = "hotel-availability-readmodel"):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self.repository = HotelAvailabilityRepository()

    async def start(self):
        await self.repository.seed_from_rooms()
        self._consumer = AIOKafkaConsumer(
            self.topic,
            group_id=self.group_id,
            bootstrap_servers=self.bootstrap_servers,
            enable_auto_commit=True,
            auto_offset_reset="earliest",
        )
        await self._consumer.start()
        self._running = True
        self._task = asyncio.create_task(self._consume())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._consumer:
            await self._consumer.stop()

    async def _consume(self):
        if not self._consumer:
            return
        try:
            async for msg in self._consumer:
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
