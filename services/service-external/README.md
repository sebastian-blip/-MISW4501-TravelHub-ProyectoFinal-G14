# Service External (integraciones)

Un único proceso FastAPI que expone las integraciones que antes vivían en microservicios separados.

**Mocks:** las rutas HTTP usan adaptadores stub o configurables; no llaman a proveedores reales salvo que cambies la estrategia por variable de entorno.

**Layout** (alineado con service-core: todo en la raíz del servicio)

- `main.py` — crea la app FastAPI y registra rutas.
- `routes/` — adaptadores **entrantes** (HTTP): un módulo por integración (`pms.py`, `payment.py`, …).
- `domains/<integración>/` — **puertos** (`ports/`) + **adaptadores salientes** (`adapters/`, factory) + `contracts.py` (Pydantic DTOs) y clientes *stub* donde aplica.
- `infrastructure/messaging/kafka/` — consumidor de **los mismos tópicos de reserva que service-core** (ver abajo).
- `resilience.py` — utilidades compartidas (`CircuitBreaker`, `retry_with_backoff`) para adaptadores salientes.

`GET /health` devuelve `integrations` con la estrategia de adaptador por integración.

### Kafka (mismos tópicos que service-core)

Los nombres coinciden con `services/service-core/infrastructure/messaging/kafka/producer.py` y `reply_consumer.py`:

| Tópico | Rol |
|--------|-----|
| `reservation-validate-requests` | **service-core** publica la solicitud; **service-external** (o service-test) consume. |
| `reservation-validate-results` | El consumidor responde aquí con el mismo `correlation_id` para que **service-core** la reciba en su reply consumer. |

Comportamiento mock en service-external: `exists` **aleatorio** (`TH_MOCK_RESERVATION_EXISTS_RATE`, default `0.25`). Si `exists=true`, se devuelve un `confirmation_code` ficticio; **sin BD**.

**Importante:** no ejecutes a la vez el consumidor de reservas de **service-test** y el de **service-external** sobre el mismo clúster si ambos consumen `reservation-validate-requests` con *consumer groups* distintos: service-core recibiría **dos** respuestas por `correlation_id`. Usa solo uno u otro.

Variables Kafka: `KAFKA_ENABLED`, `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_USERNAME`, `KAFKA_PASSWORD`; `TH_CONSUME_RESERVATION_VALIDATE` (`true`/`false`).

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
