# TravelHub — Proyecto Final MISW4501 (G14)

Repositorio del proyecto final **TravelHub**: pruebas de concepto (PoC) de arquitectura para reservas de hoteles, consistencia eventual y cumplimiento normativo (GDPR/LGPD).

## Estructura del repositorio

Cada carpeta `poc*` es una prueba de concepto independiente con su propio stack y documentación:

| Carpeta | Descripción |
|---------|-------------|
| [**poc1**](laboratorios/poc1/README.md) | Reservas de hoteles con **CQRS** y consistencia eventual: API FastAPI, PostgreSQL, Kafka, modelo de lectura de disponibilidad, Locust y Prometheus/Grafana. |
| [**poc5-gdpr**](poc5-gdpr/README.md) | Experimento **derecho al olvido** (GDPR/LGPD): User Service, Reader, Reservations y Analytics consumiendo eventos vía Redis Streams, con auditoría y métrica TFO. |

Cada PoC se ejecuta desde su propia carpeta (p. ej. `docker compose` dentro de `poc1` o `poc5-gdpr`). No hay un único `docker-compose` en la raíz.

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
