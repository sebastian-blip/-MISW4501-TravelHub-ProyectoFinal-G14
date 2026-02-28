from typing import List, Optional
from poc1.domain.models.hotel import Hotel


class HotelRepository:

    async def get_all(self) -> List[Hotel]:
        return await Hotel.all()

    async def get_by_id(self, hotel_id: str) -> Optional[Hotel]:
        return await Hotel.get_or_none(id=hotel_id)

    async def get_by_city(self, city: str) -> List[Hotel]:
        return await Hotel.filter(city=city, active=True)