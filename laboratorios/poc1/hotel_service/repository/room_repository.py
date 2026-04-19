from typing import Optional
from domain.models.hotel import Room


class RoomRepository:

    async def get_by_id(self, room_id: str) -> Optional[Room]:
        return await Room.filter(id=room_id).prefetch_related("hotel").first()
