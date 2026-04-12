# Service External (integraciones)

Un único proceso FastAPI que expone las integraciones que antes vivían en microservicios separados.

**Mocks:** las rutas HTTP y el flujo Kafka de pago/PMS **no llaman** a proveedores reales; las respuestas son locales (stubs HTTP y aleatoriedad configurable en el consumidor de booking). La BD solo se usa para reflejar el resultado simulado cuando corresponde.

**Layout** (alineado con service-core: todo en la raíz del servicio)

- `main.py` — crea la app FastAPI y registra rutas.
- `routes/` — adaptadores **entrantes** (HTTP): un módulo por integración (`pms.py`, `payment.py`, …).
- `domains/<integración>/` — **puertos** (`ports/`) + **adaptadores salientes** (`adapters/`, factory) + `contracts.py` (Pydantic DTOs) y clientes *stub* donde aplica.
- `infrastructure/` — Kafka + **PostgreSQL opcional** solo para el consumidor `booking-integration-requests` (escribe `pms_sync_logs`, y si existe la reserva: `payments`, `payment_transactions`, `reservations`, `inventory_calendar` cuando el mock PMS y el pago lo permiten).
- `domain/models/` — SQLModel mínimo alineado con `schemas/db.sql` para ese consumidor.
- `resilience.py` — utilidades compartidas (`CircuitBreaker`, `retry_with_backoff`) para adaptadores salientes.

`GET /health` devuelve `integrations` con la estrategia de adaptador por integración.

### Kafka (integración con service-core)

- `reservation-validate-requests` → `reservation-validate-results`: `exists` **aleatorio** (tasa `TH_MOCK_RESERVATION_EXISTS_RATE`, default `0.25`). Si `exists=true`, devuelve un `confirmation_code` ficticio; **sin BD**.
- `booking-integration-requests` → `booking-integration-results`: **pago y PMS 100 % mock** (sin APIs externas); éxito/fracaso **independiente y aleatorio** (`TH_MOCK_PAYMENT_SUCCESS_RATE`, `TH_MOCK_PMS_SUCCESS_RATE`, default `0.7`). Si `TH_BOOKING_DB_UPDATES=true` (default), se escribe en BD: **`pms_sync_logs`** según mock PMS; si la reserva existe, **`payments`** / **`payment_transactions`** usan **`total_price` y `currency_code` de la reserva** (ISO 4217 normalizado); **`reservations`** según mock de pago; si **pago OK y PMS OK**, se decrementa **`inventory_calendar`** solo en filas cuyo **`currency_code`** coincide con la moneda del cobro. El resultado Kafka incluye `amount`, `currency_code`, `db_commit_ok`, `db_error`.

Variables BD: `POSTGRES_*`, `POSTGRES_SSL` (`require` por defecto para RDS; usar `disable` en local sin SSL). `TH_BOOKING_DB_UPDATES=false` desactiva cualquier escritura (solo Kafka).

**Importante:** no ejecutes a la vez el consumidor de reservas de **service-test** y el de **service-external** sobre el mismo clúster si ambos consumen `reservation-validate-requests` con *consumer groups* distintos: service-core recibiría **dos** respuestas por `correlation_id`. Usa solo uno u otro.

Variables Kafka: `KAFKA_ENABLED`, `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_USERNAME`, `KAFKA_PASSWORD`; `TH_CONSUME_RESERVATION_VALIDATE`, `TH_CONSUME_BOOKING_INTEGRATION` (`true`/`false`).

**service-core** suscribe también a `booking-integration-results` y, tras crear la reserva, **espera** la respuesta con el mismo `correlation_id` (timeout `TH_BOOKING_REPLY_TIMEOUT` segundos, default 30). Crea el tópico `booking-integration-results` en el clúster si no existe.

## Rutas (prefijo → antes)

| Prefijo | Ejemplo | Notas |
|---------|---------|--------|
| `/pms` | `GET /pms/v1/catalog/{hotel_external_id}` | |
| `/payment` | `POST /payment/v1/payment-intents` | |
| `/currency` | `GET /currency/v1/rates?base=USD&quote=COP` | |
| `/cdn-storage` | `POST /cdn-storage/v1/signed-urls` | |
| `/maps` | `GET /maps/v1/geocode?...` | |
| `/notification` | `POST /notification/v1/notifications/email` | |

Salud global: `GET /health`, `GET /ready`.

## Variables de entorno (estrategia por integración)

Cada integración elige adaptador con su propia variable (evita colisiones con un solo `ADAPTER_STRATEGY`):

- `PMS_ADAPTER_STRATEGY` (default `pms`)
- `PAYMENT_ADAPTER_STRATEGY` (default `gateway`)
- `CURRENCY_ADAPTER_STRATEGY` (default `exchange`)
- `CDN_STORAGE_ADAPTER_STRATEGY` (default `cdn`)
- `MAPS_ADAPTER_STRATEGY` (default `maps`)
- `NOTIFICATION_ADAPTER_STRATEGY` (default `email_sms`)

Opcional: `TH_PAYMENT_SKIP_READY` para el comportamiento legacy del readiness de pago.

## Docker

Contexto de build = carpeta del servicio (el `Dockerfile` hace `COPY . .` sobre `services/service-external`):

```bash
docker build -f services/service-external/Dockerfile -t service-external:local services/service-external
```

## Kubernetes

Manifiestos en `k8s/`. Secret opcional: `service-external-secrets` (`envFrom`).