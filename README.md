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
