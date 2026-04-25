# TravelHub — Proyecto Final MISW4501 (G14)

Repositorio del proyecto final **TravelHub**: pruebas de concepto (PoC) de arquitectura para reservas de hoteles, consistencia eventual y cumplimiento normativo (GDPR/LGPD).

## Estructura del repositorio

Cada carpeta `poc*` es una prueba de concepto independiente con su propio stack y documentación:

| Carpeta | Descripción |
|---------|-------------|
| [**poc1**](laboratorios/poc1/README.md) | Reservas de hoteles con **CQRS** y consistencia eventual: API FastAPI, PostgreSQL, Kafka, modelo de lectura de disponibilidad, Locust y Prometheus/Grafana. |
| [**poc5-gdpr**](poc5-gdpr/README.md) | Experimento **derecho al olvido** (GDPR/LGPD): User Service, Reader, Reservations y Analytics consumiendo eventos vía Redis Streams, con auditoría y métrica TFO. |

Cada PoC se ejecuta desde su propia carpeta (p. ej. `docker compose` dentro de `poc1` o `poc5-gdpr`).

### Servicios `service-core` + `service-external` (stack local)

La base de datos del stack completo es **RDS** (o el host que definas): credenciales solo en **`.env`** (no subir al repo). Copia `.env.example` → `.env` y completa `POSTGRES_PASSWORD`.

```bash
cp .env.example .env
# editar .env
docker compose -f docker-compose.full-stack.yml up -d --build
./scripts/full-stack-seed-and-smoke.sh
```

- API core: http://localhost:8000/docs — flujo `POST /reservation-flow/create`
- API external: http://localhost:8002/docs
- Kafka en Docker: **core** y **external** usan PLAINTEXT si `KAFKA_USERNAME`/`KAFKA_PASSWORD` están vacíos (comportamiento alineado). `FULL_STACK_CORE_KAFKA` por defecto **true** en `docker-compose.full-stack.yml` para probar `reservation-validate-*`. Con MSK, define usuario, contraseña y `KAFKA_BOOTSTRAP_SERVERS`.
- Infra solo Postgres+Kafka en local (sin apps): `docker-compose.local-dev.yml`.

#### Compose mínimo para correr 100% local (`docker-compose.local.yml`)

Este repo incluye `docker-compose.local.yml` para levantar **Postgres + Kafka (PLAINTEXT) + service-core + service-external** sin MSK ni certificados.

- **Reset total + carga de schema + seeds (recomendado para correr “from scratch”)**:

```bash
# 1) reset total (borra el volumen de Postgres)
docker compose -f docker-compose.local.yml down -v

# 2) levanta SOLO postgres
docker compose -f docker-compose.local.yml up -d postgres

# 3) crea schema y seeds en esa DB
docker exec -i misw4501-travelhub-proyectofinal-g14-postgres-1 psql -U postgres -d travelhub -f - < schemas/db.sql
docker exec -i misw4501-travelhub-proyectofinal-g14-postgres-1 psql -U postgres -d travelhub -f - < schemas/seed_hotels.sql
docker exec -i misw4501-travelhub-proyectofinal-g14-postgres-1 psql -U postgres -d travelhub -f - < schemas/seed_reservations.sql

# 4) ahora sí levanta los servicios
docker compose -f docker-compose.local.yml up -d --build service-core service-external
```

- **Sin Kafka** (por defecto):

```bash
docker compose -f docker-compose.local.yml up -d --build
```

- **Con Kafka local**:

```bash
KAFKA_ENABLED=true docker compose -f docker-compose.local.yml --profile kafka up -d --build
```

Endpoints:
- Core: http://localhost:8000/docs
- External: http://localhost:8002/docs

## Cómo empezar

1. Elige la PoC que quieras ejecutar.
2. Entra en su carpeta y sigue el README correspondiente:
   - **poc1:** reservas y búsqueda de disponibilidad, carga con Locust.
   - **poc5-gdpr:** experimento de derecho al olvido con usuario de prueba y consulta de TFO.

## Requisitos generales

- Docker y Docker Compose
- Para **poc1** con Locust en el host: Python 3.12 y dependencias en `poc1/requirements.txt` (opcional si solo usas los contenedores)

## Autores

Grupo 14 — Maestría en Ingeniería de Software (MISO).
