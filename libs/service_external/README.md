# `service_external` (hexagonal)

Librería compartida para integraciones con terceros. **No** es un microservicio: no tiene Dockerfile ni carpeta en `k8s/`.

## Estructura

| Carpeta | Rol |
|---------|-----|
| `ports/` | Interfaces que la aplicación necesita (ej. `PaymentPort`, `LocationPort`). |
| `contracts/` | DTOs / modelos compartidos entre puertos y adaptadores. |
| `adapters/` | Implementaciones concretas que llaman a APIs externas. |

Cada **microservicio** adapter vive en `services/service-external/<nombre>/` (K8s: `k8s/<nombre>/`) e importa este paquete Python `service_external`.
