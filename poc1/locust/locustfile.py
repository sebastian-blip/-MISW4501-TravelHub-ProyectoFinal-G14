from locust import HttpUser, task, between, events, constant
import random
import uuid
from datetime import date, timedelta
from threading import Lock
import time

# ciudades usadas para el experimento
CITIES = ["Cali", "Bogotá"]

lock = Lock()
reserved_rooms = {}
pending_checks = {}
reported_inconsistencies = set()

# métricas del experimento
total_reservations = 0
total_reads = 0
inconsistent_reads = 0
consistency_delays = []
inconsistent_reservations = 0
resolved_reservations = 0
MIN_CONSISTENCY_DELAY = 4


def random_dates():
    check_in = date.today()
    check_out = check_in + timedelta(days=random.randint(1, 3))
    return str(check_in), str(check_out)


class WriterUser(HttpUser):

    wait_time = constant(1)

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
                reserved_rooms[key] = {
                    "created_at": time.time(),
                    "city": city,
                    "reported": False,
                }
                total_reservations += 1

            print(f"✅ Reservation created {key}")


class ReaderUser(HttpUser):

    wait_time = constant(10)

    @task
    def buscar_disponibilidad(self):

        global total_reads
        global inconsistent_reads
        global inconsistent_reservations
        global resolved_reservations

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

        now = time.time()
        with lock:
            reserved_copy = {key: value.copy() for key, value in reserved_rooms.items()}

        found_inconsistency = False

        for key, info in reserved_copy.items():

            if info["city"] != city:
                continue

            delay = now - info["created_at"]

            if delay < MIN_CONSISTENCY_DELAY:
                continue

            if key in visible_rooms:

                found_inconsistency = True

                if not info["reported"]:

                    reported_inconsistencies.add(key)

                    with lock:
                        reserved_rooms[key]["reported"] = True
                        inconsistent_reservations += 1

                    print(
                        f"⚠️ Inconsistency detected for {key} "
                        f"(delay {round(now - info['created_at'],2)}s)"
                    )
            else:

                with lock:
                    consistency_delays.append(delay)
                    resolved_reservations += 1
                    reserved_rooms.pop(key, None)

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

    print(f"Inconsistent reservations observed: {inconsistent_reservations}")
    print(f"Resolved reservations: {resolved_reservations}/{total_reservations}")
    print(f"Pending consistency checks: {len(reserved_rooms)}")

    if consistency_delays:
        avg_delay = sum(consistency_delays) / len(consistency_delays)
        print(f"Average consistency delay: {round(avg_delay,2)} seconds")
        print(f"Max delay observed: {round(max(consistency_delays),2)} seconds")

    print("============================")
