from locust import HttpUser, task, between
import random
import string
import datetime

# Parámetros editables (puedes cambiar rangos de fecha, ciudades, etc)
CITIES = ["Paris", "New York", "London", "Tokyo", "Medellin", "CDMX"]
GUEST_IDS = [    # Lista o puedes generar randoms
    ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    for _ in range(100)
]

def random_date(days_ahead=90):
    start = datetime.date.today()
    check_in = start + datetime.timedelta(days=random.randint(1, days_ahead))
    check_out = check_in + datetime.timedelta(days=random.randint(1, 7))
    return check_in.strftime('%Y-%m-%d'), check_out.strftime('%Y-%m-%d')

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)   # Delay entre requests por usuario, ajústalo según lo que busques medir

    @task
    def search_accommodation(self):
        city = random.choice(CITIES)
        check_in, check_out = random_date()
        guests = random.randint(1, 6)
        guest_id = random.choice(GUEST_IDS)

        headers = {
            "X-Guest-Id": guest_id
        }
        params = {
            "city": city,
            "check_in": check_in,
            "check_out": check_out,
            "guests": guests
        }
        with self.client.get(
            "/service-core/accommodations/search",
            headers=headers,
            params=params,
            name="/service-core/accommodations/search",   # Agrupa stats
            catch_response=True,
            timeout=10
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
