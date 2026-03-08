import json
from typing import Any
from abc import ABC, abstractmethod

# default kafka topic
DEFAULT_TOPIC = "reservation-created"


class EventPublisherABC(ABC):
    @abstractmethod
    async def publish(self, event: Any) -> None:
        raise NotImplementedError


class InMemoryPublisher(EventPublisherABC):
    # fallback publisher used for testing/local development
    async def publish(self, event: Any) -> None:
        print("[InMemoryPublisher] Event published:", json.dumps(event.to_dict()))


_singleton: EventPublisherABC | None = None


class EventPublisher:
    """Simple registry to get a publisher instance. By default uses InMemoryPublisher.

    Call `EventPublisher.set(publisher_instance)` in app startup to wire a concrete
    Kafka producer implementation.
    """

    @staticmethod
    def get() -> EventPublisherABC:
        global _singleton
        if _singleton is None:
            _singleton = InMemoryPublisher()
        return _singleton

    @staticmethod
    def set(publisher: EventPublisherABC):
        global _singleton
        _singleton = publisher
