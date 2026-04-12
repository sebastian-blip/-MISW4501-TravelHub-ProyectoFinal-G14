from prometheus_client import Counter, Histogram


reservations_created_total = Counter(
    "reservations_created_total",
    "Total number of reservations created",
)

reservations_consumed_total = Counter(
    "reservations_consumed_total",
    "Total number of reservation events consumed",
)

availability_checks_total = Counter(
    "availability_checks_total",
    "Total number of hotel availability checks",
)

reservation_consistency_lag_seconds = Histogram(
    "reservation_consistency_lag_seconds",
    "Lag between reservation creation and consumption",
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)
