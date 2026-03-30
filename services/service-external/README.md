# Service External (integraciones)

Un único proceso FastAPI que expone las integraciones que antes vivían en microservicios separados.

**Layout**

- `app/main.py` — crea la app y registra rutas.
- `app/routes/` — adaptadores **entrantes** (HTTP): un módulo por integración (`pms.py`, `payment.py`, …).
- `app/domains/<integración>/` — **puertos** (`ports/`) + **adaptadores salientes** (`adapters/`, factory). No es el “dominio DDD” completo: son *rebanadas* de integración (hexagonal outbound).

`GET /health` devuelve `integrations` con la estrategia de adaptador por integración.

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

Desde la raíz del monorepo (el `Dockerfile` copia `libs/service_external`):

```bash
docker build -f services/service-external/Dockerfile -t service-external:local .
```

## Kubernetes

Manifiestos en `k8s/`. Secret opcional: `service-external-secrets` (`envFrom`).
