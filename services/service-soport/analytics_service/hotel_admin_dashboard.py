from collections import Counter, defaultdict

def bookings_stats(bookings, allowed_status=("confirmed",)):
    total_reservas = 0
    total_personas = 0
    total_ganancias = 0.0

    estados_contador = Counter()

    for b in bookings:
        status = b.get("status")
        guests = int(b.get("guests", 0))
        total_price = float(b.get("total_price", 0.0))

        total_reservas += 1
        estados_contador[status] += 1
        if status in allowed_status:
            total_personas += guests
            total_ganancias += total_price

    percent_status = {}
    for estado, count in estados_contador.items():
        porcentaje = round((count / total_reservas) * 100, 2) if total_reservas else 0.0
        percent_status[estado] = f'{porcentaje}%'

    ingresos_dia = revenue_per_day(bookings)

    return {
        "total_reservas": total_reservas,
        "total_personas": total_personas,
        "total_ganancias": round(total_ganancias, 2),
        "percent_status": percent_status,
        'revenue_per_day': ingresos_dia,
    }


def revenue_per_day(bookings, status_ok=("confirmed",)):
    """
    Retorna una lista de ingresos por día de check-in, solo para reservas en estados de status_ok.
    [
      {"date": "2026-05-05", "revenue": 525.0},
      {"date": ...}
    ]
    """
    ingresos = defaultdict(float)
    for b in bookings:
        status = b.get("status")
        if status in status_ok:
            date = b.get("check_in")  # str tipo '2026-05-05'
            total_price = float(b.get("total_price", 0.0))
            ingresos[date] += total_price

    return [{"date": d, "revenue": round(ing, 2)} for d, ing in sorted(ingresos.items())]
