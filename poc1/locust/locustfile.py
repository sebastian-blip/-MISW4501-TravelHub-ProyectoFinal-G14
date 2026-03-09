from locust import HttpUser, task, between, events
import random
import uuid
from datetime import date, timedelta
from threading import Lock
import time

# ciudades usadas para el experimento
CITIES = ["Cali", "Bogotá"]

# almacenamiento compartido
reserved_rooms = {}
reported_inconsistencies = set()

lock = Lock()

# métricas del experimento
total_reservations = 0
total_reads = 0
inconsistent_reads = 0
consistency_delays = []


def random_dates():
    check_in = date.today()
    check_out = check_in + timedelta(days=random.randint(1, 3))
    return str(check_in), str(check_out)


class WriterUser(HttpUser):

    weight = 1
    wait_time = between(0.5, 1.5)

    @task
    def reservar_habitacion(self):

        global total_reservations

        city = random.choice(CITIES)

        response = self.client.get(
            f"/hotels/search?city={city}",
            name="/hotels/search"
        )

        if response.status_code != 200:
            return

        availability = response.json()

        if not availability:
            return

        room = random.choice(availability)

        hotel_id = room["hotel_id"]
        room_id = room["room_id"]

        check_in, check_out = random_dates()

        payload = {
            "hotel_id": hotel_id,
            "room_id": room_id,
            "user_id": str(uuid.uuid4()),
            "check_in": check_in,
            "check_out": check_out,
            "total_price": random.randint(100, 300),
        }

        response = self.client.post(
            "/reservations",
            json=payload,
            name="/reservations"
        )

        if response.status_code in (200, 201):

            key = f"{hotel_id}-{room_id}"

            with lock:
                reserved_rooms[key] = time.time()
                total_reservations += 1

            print(f"✅ Reservation created {key}")


class ReaderUser(HttpUser):

    weight = 10
    wait_time = between(0.2, 1)

    @task
    def buscar_disponibilidad(self):

        global total_reads
        global inconsistent_reads

        city = random.choice(CITIES)

        response = self.client.get(
            f"/hotels/search?city={city}",
            name="/hotels/search"
        )

        if response.status_code != 200:
            return

        availability = response.json()

        visible_rooms = {
            f"{room['hotel_id']}-{room['room_id']}" for room in availability
        }

        with lock:
            reserved_copy = reserved_rooms.copy()

        found_inconsistency = False

        for key, reservation_time in reserved_copy.items():

            if key in visible_rooms:

                found_inconsistency = True

                if key not in reported_inconsistencies:

                    reported_inconsistencies.add(key)

                    delay = time.time() - reservation_time

                    with lock:
                        consistency_delays.append(delay)

                    print(
                        f"⚠️ Inconsistency detected for {key} "
                        f"(delay {round(delay,2)}s)"
                    )

        with lock:
            total_reads += 1

            if found_inconsistency:
                inconsistent_reads += 1


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):

    print("\n============================")
    print("EXPERIMENT RESULTS")
    print("============================")

    print(f"Total reservations: {total_reservations}")
    print(f"Total reads: {total_reads}")
    print(f"Inconsistent reads: {inconsistent_reads}")

    if total_reads > 0:
        rate = (inconsistent_reads / total_reads) * 100
        print(f"Inconsistency rate: {round(rate,2)} %")

    if consistency_delays:
        avg_delay = sum(consistency_delays) / len(consistency_delays)
        print(f"Average consistency delay: {round(avg_delay,2)} seconds")
        print(f"Max delay observed: {round(max(consistency_delays),2)} seconds")

    print("============================")