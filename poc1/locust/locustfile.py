from locust import HttpUser, task, between
import random
import uuid
from datetime import date, timedelta

# ciudades usadas para el experimento
CITIES = ["Cali", "Bogotá"]





def random_dates():
    check_in = date.today()
    check_out = check_in + timedelta(days=random.randint(1, 3))
    return str(check_in), str(check_out)


class WriterUser(HttpUser):
    """
    Usuario A
    Simula un usuario que realiza reservas
    """
    wait_time = between(0.5, 1.5)

    @task
    def reservar_habitacion(self):

        city = random.choice(CITIES)

        # 1 buscar hoteles disponibles por ciudad

        response = self.client.get(
            f"/hotels/search?city={city}",
            name="/hotels"
        )

        if response.status_code != 200:
            return


        availability = response.json()

        if not availability:
            return

        hotel_room = random.choice(availability)
        hotel_id = hotel_room["hotel_id"]
        room_id = hotel_room["room_id"]

        # 3 crear reserva
        check_in, check_out = random_dates()

        reservation_payload = {
            "hotel_id": hotel_id,
            "room_id": room_id,
            "user_id": str(uuid.uuid4()),
            "check_in": check_in,
            "check_out": check_out,
            "total_price": random.randint(100, 300),
        }


        self.client.post(
            "/reservations",
            json=reservation_payload,
            name="/reservations"
        )


class ReaderUser(HttpUser):
    """
    Usuario B
    Simula usuarios que solo consultan disponibilidad
    """
    wait_time = between(0.2, 1)

    @task
    def buscar_disponibilidad(self):

        city = random.choice(CITIES)

        # 1 buscar hoteles
        response = self.client.get(
            f"/hotels/search?city={city}",
            name="/hotels"
        )

        if response.status_code != 200:
            return

