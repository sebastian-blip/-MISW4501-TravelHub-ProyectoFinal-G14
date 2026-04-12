# PoC-1 — Hotel reservations & availability (CQRS + eventual consistency)

Proof of concept for the TravelHub hotel reservation flow with **CQRS** and **eventual consistency**: writes go to PostgreSQL and are published to Kafka; a read model (availability) is updated by a Kafka consumer and exposed via the same API.

## Stack

- **API:** FastAPI (Python 3.12)
- **Database:** PostgreSQL 16
- **Messaging:** Apache Kafka (Confluent)
- **Observability:** Prometheus + Grafana
- **Load testing:** Locust

## Architecture

- **Commands:** Create reservation → persisted in PostgreSQL, event `ReservationCreated` published to Kafka topic `reservation-created`.
- **Read model:** `AvailabilityReadModelConsumer` consumes from `reservation-created`, updates the availability store (in-memory/DB), so that `GET /hotels/search?city=...` reflects eventual consistency.
- **Queries:** Hotels list, search by city (from availability read model), get reservation by ID.

## How to run

```bash
cd poc1
docker compose up --build
```

- **API:** http://localhost:8000  
- **Prometheus:** http://localhost:9090  
- **Grafana:** http://localhost:3000  

## Main endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hotels` | List hotels (optional `?city=`) |
| GET | `/hotels/search?city={city}` | Search available rooms by city (read model) |
| POST | `/reservations` | Create reservation (command) |
| GET | `/reservations/{id}` | Get reservation by ID |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |

## Load test (Locust)

From the project root (or `poc1`), with the stack running:

```bash
cd poc1
locust -f locust/locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089, spawn users (WriterUser + ReaderUser). The locustfile simulates writers creating reservations and readers querying availability, and reports inconsistency metrics (eventual consistency delay, inconsistency rate).

## Project layout

| Path | Description |
|------|-------------|
| `main.py` | FastAPI app, DB init, Kafka producer, availability consumer |
| `routes/` | Hotel and reservation routers (queries + commands) |
| `hotel_service/` | Commands, queries, events, availability read model & consumer |
| `domain/models/` | Hotel, reservation, hotel_availability |
| `infrastructure/` | Tortoise ORM config, Kafka producer |
| `locust/` | Locustfile for load and consistency experiment |
| `prome_poc1/` | Prometheus config (scrapes API metrics) |
| `init.sql` | PostgreSQL schema and seed data |

## Environment

- `KAFKA_BOOTSTRAP_SERVERS` — default `travelhub_kafka:9092` (use `localhost:9092` when running Locust on host).
- `POSTGRES_*` — set by `docker-compose` for the API container.
