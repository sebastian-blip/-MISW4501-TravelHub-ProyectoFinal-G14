import random
import uuid
from datetime import date, timedelta, time
from decimal import Decimal
from pathlib import Path

import polars as pl
from sqlmodel import select

from src.database import db
from src.models.hotel import Hotel
from src.models.inventory_calendar import InventoryCalendar
from src.models.room_type import RoomType
from src.models.user import User

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
COUNTRY_ID = uuid.UUID("ac9762f9-cc07-4024-8ee0-840dc90e21dd")
HOTEL_COUNT = 15
ROOM_TYPES_PER_HOTEL = (2, 5)
CALENDAR_DAYS = 90

CITIES = [
    "Bogotá",
    "Medellín",
    "Cartagena",
    "Cali",
    "Santa Marta",
    "Barranquilla",
    "Bucaramanga",
    "Pereira",
    "Manizales",
    "Villavicencio",
]

ROOM_NAMES = ["Standard", "Deluxe", "Suite", "Superior", "Executive", "Family", "Presidential"]
BED_TYPES = ["King", "Queen", "Twin", "Double", "Sofa Bed", "Bunk Bed"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_mock_names():
    df = pl.read_json(BASE_DIR / "src" / "data" / "MOCK_DATA.json")
    return df["hotel_name"].to_list()


def random_hotel_name(names: list[str]) -> str:
    """Generate a hotel name by combining two random mock names + Colombia."""
    first = random.choice(names)
    second = random.choice(names)
    return f"{first} {second} Hotel"


def random_address() -> str:
    street_types = ["Calle", "Carrera", "Avenida", "Diagonal", "Transversal"]
    return f"{random.choice(street_types)} {random.randint(1, 150)} #{random.randint(1, 99)}-{random.randint(1, 50)}"


def random_phone() -> str:
    return f"+57 {random.randint(300, 399)} {random.randint(1000000, 9999999)}"


def random_email(hotel_name: str) -> str:
    slug = hotel_name.lower().replace(" ", "-").replace("hotel", "")
    return f"reservas@{slug}colombia.com"


def create_hotel(names: list[str], owner_id: uuid.UUID | None = None) -> Hotel:
    city = random.choice(CITIES)
    name = random_hotel_name(names)
    return Hotel(
        name=name,
        description=f"Hermoso hotel ubicado en {city}, Colombia. Ideal para turismo y negocios.",
        address=random_address(),
        city=city,
        country_id=COUNTRY_ID,
        latitude=Decimal(str(round(random.uniform(3.0, 11.0), 8))),
        longitude=Decimal(str(round(random.uniform(-77.5, -72.5), 8))),
        phone=random_phone(),
        email=random_email(name),
        stars=random.randint(2, 5),
        rating=Decimal(str(round(random.uniform(3.0, 5.0), 1))),
        total_reviews=random.randint(10, 500),
        check_in_time=time(15, 0),
        check_out_time=time(11, 0),
        owner_user_id=owner_id,
        pms_provider=random.choice([None, "Cloudbeds", "SiteMinder", "Oracle Hospitality"]),
        active=True,
    )


def create_room_type(hotel_id: uuid.UUID) -> RoomType:
    name = random.choice(ROOM_NAMES)
    base_price = Decimal(str(round(random.uniform(80, 500), 2)))
    return RoomType(
        hotel_id=hotel_id,
        name=name,
        description=f"Habitación {name.lower()} con todas las comodidades.",
        base_price=base_price,
        max_capacity=random.randint(1, 6),
        bed_type=random.choice(BED_TYPES),
        size_sqm=Decimal(str(round(random.uniform(20, 120), 1))),
        total_units=random.randint(5, 50),
        active=True,
    )


def create_inventory_entries(room_type_id: uuid.UUID, base_price: Decimal):
    entries = []
    today = date.today()
    for i in range(CALENDAR_DAYS):
        entry_date = today + timedelta(days=i)
        # Add some price variance
        variance = Decimal(str(round(random.uniform(-20, 50), 2)))
        price = max(Decimal("50.00"), base_price + variance)
        entries.append(
            InventoryCalendar(
                room_type_id=room_type_id,
                date=entry_date,
                available_units=random.randint(0, 30),
                price_per_night=price,
                currency_code="USD",
                minimum_stay=random.randint(1, 3),
            )
        )
    return entries


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    session = db.get_session()

    # Fetch existing users to use as owners
    users = session.exec(select(User)).all()
    owner_ids = [u.id for u in users if u.user_type in ("hotel_admin", "admin")] or [u.id for u in users]

    names = load_mock_names()

    print(f"Found {len(users)} users. Generating {HOTEL_COUNT} hotels...")

    hotels = []
    room_types = []
    inventory_entries = []

    for _ in range(HOTEL_COUNT):
        owner_id = random.choice(owner_ids) if owner_ids else None
        hotel = create_hotel(names, owner_id=owner_id)
        hotels.append(hotel)

        num_room_types = random.randint(*ROOM_TYPES_PER_HOTEL)
        for _ in range(num_room_types):
            rt = create_room_type(hotel.id)
            room_types.append(rt)
            inventory_entries.extend(create_inventory_entries(rt.id, rt.base_price))

    print(f"Inserting {len(hotels)} hotels, {len(room_types)} room types, {len(inventory_entries)} inventory entries...")

    for hotel in hotels:
        session.add(hotel)
    for rt in room_types:
        session.add(rt)
    for entry in inventory_entries:
        session.add(entry)

    session.commit()
    session.close()

    print("Done!")


if __name__ == "__main__":
    main()
