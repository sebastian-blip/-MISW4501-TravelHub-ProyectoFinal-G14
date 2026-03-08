import uuid
import random
from domain.models.hotel import Hotel
from domain.models.hotel_availability import HotelAvailability

CIUDADES = ["Cali", "Bogotá"]

async def seed_hotels():

    for x in range(10000):
        ciudad = random.choice(CIUDADES)
        hotel_id = uuid.uuid4()
        hotel = await Hotel.create(
            id=hotel_id,
            name="Hilton Cali",
            city=ciudad,
            country="COL",
            address="Av Colombia 1-40",
            stars=5
        )

        await HotelAvailability.create(
            id=uuid.uuid4(),
            hotel_id=hotel_id,
            room_id=uuid.uuid4(),
            hotel_name=hotel.name,
            city=hotel.city,
            available=True,
            room_type="Deluxe",
            price_per_night=120.00
        )

        await HotelAvailability.create(
            id=uuid.uuid4(),
            hotel_id=hotel_id,
            room_id=uuid.uuid4(),
            hotel_name=hotel.name,
            city=hotel.city,
            available=True,
            room_type="Suite",
            price_per_night=250.00
        )