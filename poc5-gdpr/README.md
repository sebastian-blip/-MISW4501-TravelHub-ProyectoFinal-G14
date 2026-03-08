# PoC-5 GDPR / LGPD — Derecho al olvido (experimento)

Experimento de arquitectura para validar el **derecho al olvido** y la **auditoría** en red distribuida (Historia A5). Solo los componentes del experimento: User Service (writer), Reader, Reservations, Analytics + **Redis** (Redis Streams) + auditoría.

## Estilo por servicio (Vista Funcional)

| Carpeta | Estilo |
|---------|--------|
| `core_user_service/` | Core: `routes/`, `services/`, `repositories/` |
| `core_reader_service/` | Core: CQRS read model (consumidor) |
| `core_reservations_consumer/` | Core: consumidor + repositories |
| `apoyo_analytics_consumer/` | Apoyo: hexagonal `domain/`, `ports/`, `adapters/` |

## Cómo ejecutar

```bash
cd poc5-gdpr
docker compose up --build
```

- **User Service API (core):** http://localhost:8000  
- **Redis:** localhost:6379 (stream `stream:usuario_olvidado`, consumer groups: reader, reservations, analytics)  
- **DB (DuckDB):** http://localhost:8080 (API del servicio `db`; almacén DuckDB en `/data`)

## Flujo

1. `POST /users/{user_id}/derecho-olvido` → User Service anonimiza, publica evento `UsuarioOlvidado`, registra T0 en auditoría.
2. Reader, Reservations y Analytics consumen el evento, anonimizan su modelo y registran "completado" en auditoría.
3. **TFO** = max(T1, T2, T3) − T0. Meta: **&lt; 3 minutos**.

## Consultar TFO

```bash
curl http://localhost:8000/audit/tfo/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11
```

## Usuario de prueba

- **ID:** `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11`  
- Creado por el servicio `db` (DuckDB) al iniciar. Ejecutar derecho al olvido contra este ID para probar el happy path.
