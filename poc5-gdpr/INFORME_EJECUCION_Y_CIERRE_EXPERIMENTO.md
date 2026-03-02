# Informe: Ejecución y cierre del experimento PoC-5 (Derecho al olvido)

Guía para **correr el experimento**, **recolectar la información necesaria** y **completar el informe de avance** (resultados y conclusiones) del PoC-5 GDPR/LGPD.

**Anonimizado vs eliminado vs “olvidado”:** En este experimento el derecho al olvido se implementa como **anonimización**, no como eliminación física de registros. **Anonimizar** = quitar o enmascarar los datos que identifican a la persona (PII), de modo que la persona deja de ser identificable (“se la olvida”); los registros pueden seguir existiendo con datos anónimos (útil para integridad referencial, reservas, estadísticas). **Eliminar** = borrar las filas; en este PoC no se eliminan filas para preservar integridad referencial (p. ej. reservas) y trazabilidad. Por tanto: **“olvidar” aquí = anonimizar**; no es lo mismo que eliminar registros.

**Correr el experimento desde cero y actualizar el documento:** En `poc5-gdpr` ejecuta `./scripts/ejecutar_experimento_desde_cero.sh`. Se genera `EXPERIMENTO_SALIDA.txt` con todos los resultados y logs. Abre ese archivo, copia cada bloque (Health, Users, User read model, Reservations, Analytics, Audit events, API TFO, logs de los cuatro servicios) y pégalo en este informe en Anexo A y en Anexo B (B.1 Resultados y B.2 Logs), sustituyendo el contenido de ejemplo.

---

## 1. Cómo se corre el experimento

### 1.1 Levantar el entorno (o ejecutar todo desde cero)

**Opción recomendada — experimento desde cero (estado limpio, T1+T2+T3):**
```bash
cd poc5-gdpr
./scripts/ejecutar_experimento_desde_cero.sh
```
El script hace: `docker compose down -v` → `up -d` (seis contenedores) → espera 30 s → POST derecho-olvido → espera 10 s → escribe en `EXPERIMENTO_SALIDA.txt` todos los resultados y logs. Abre `EXPERIMENTO_SALIDA.txt` y copia cada sección al informe (Anexo A y B).

**Opción manual — solo levantar:**
```bash
cd poc5-gdpr
docker compose up -d
```

Servicios:

| Servicio | Contenedor | Puerto / URL |
|----------|------------|--------------|
| PostgreSQL | poc5_gdpr_db | localhost:5433 (DB: `poc5_gdpr`, user/pass: postgres) |
| RabbitMQ | poc5_gdpr_rabbitmq | AMQP 5672, Management http://localhost:15672 (guest/guest) |
| Core User Service | poc5_gdpr_core_user_service | http://localhost:8000 |
| Core Reader | poc5_gdpr_core_reader | consumidor (sin HTTP) |
| Core Reservations | poc5_gdpr_core_reservations | consumidor (sin HTTP) |
| Apoyo Analytics | poc5_gdpr_apoyo_analytics | consumidor (sin HTTP) |

**Para que el experimento tenga sentido, los tres consumidores (Reader, Reservations, Analytics) deben estar levantados.** Si falta alguno (por ejemplo Analytics), solo habrá 2 completados en auditoría y la corrida no es válida. Comprobar que todo esté arriba:

```bash
docker compose ps
curl -s http://localhost:8000/health
```

Verificar que aparezcan **los seis** contenedores en running: `poc5_gdpr_db`, `poc5_gdpr_rabbitmq`, `poc5_gdpr_core_user_service`, `poc5_gdpr_core_reader`, `poc5_gdpr_core_reservations`, `poc5_gdpr_apoyo_analytics`. Si falta `poc5_gdpr_apoyo_analytics`, el experimento no es válido hasta que esté levantado y se vuelva a ejecutar el derecho al olvido (tras reset de BD si hace falta).

**Si la imagen no corre (contenedor sale o no arranca):**

1. **Ejecutar desde la carpeta correcta:** siempre `cd poc5-gdpr` antes de `docker compose` (el `docker-compose.yml` y el contexto de build están ahí).
2. **Docker en marcha:** que Docker Desktop (o el daemon) esté abierto y que `docker info` responda.
3. **Diagnóstico automático:** en `poc5-gdpr` ejecuta:
   ```bash
   ./scripts/diagnostico_docker.sh
   ```
   El script hace build con salida visible, levanta primero DB y RabbitMQ, luego el resto, y muestra el estado y los logs de cualquier contenedor que haya salido (Exited). Ahí verás el error (p. ej. módulo Python faltante, conexión rechazada a postgres/rabbitmq).
4. **Revisar logs del contenedor que falla:** `docker logs poc5_gdpr_core_user_service` (o el nombre del que esté Exited). Si el contenedor sale al poco de iniciar, suele ser un error en el arranque (import, conexión a BD/ RabbitMQ).
5. **Reconstruir sin caché:** `docker compose build --no-cache` y luego `docker compose up -d`.

Los servicios tienen `restart: on-failure` en `docker-compose.yml`, así que si fallan al arrancar se reintentan y puedes ver los logs con `docker compose logs -f <nombre_servicio>`.

### 1.2 Usuario de prueba (seed)

- **User ID:** `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11`
- Creado en `init.sql` en: `users`, `user_read_model`, `reservations`, `analytics_user_activity`.

Para repetir el experimento con datos frescos, reiniciar la BD (borra datos):

```bash
docker compose down -v
docker compose up -d
# Esperar ~10 s a que init.sql cree el usuario de prueba
```

### 1.3 Ejecutar los casos (happy path y unhappy paths)

Se deben ejecutar **tres casos**: un happy path (flujo normal) y dos unhappy paths (evento perdido y consumidor lento) para documentar comportamiento y ajustes. El happy path es obligatorio; los unhappy son opcionales pero recomendados para el informe.

#### Happy path (obligatorio)

1. **Registrar estado ANTES (opcional pero recomendado para evidencias)**  
   Consultar en PostgreSQL que el usuario tenga PII:

   ```bash
   docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
     "SELECT id, email, name, anonymized FROM users WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';"
   ```

   Anotar: email y name visibles, `anonymized = false`.

2. **Disparar derecho al olvido (T0 se registra aquí)**  

   ```bash
   curl -s -X POST "http://localhost:8000/users/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/derecho-olvido"
   ```

   Respuesta esperada: `{"ok":true,"message":"Derecho al olvido aceptado. Propagación en curso.","t0":"..."}`.  
   **Anotar el valor de `t0`** (timestamp ISO).

3. **Esperar propagación**  
   Los consumidores (Reader, Reservations, Analytics) procesan el evento. En entorno local suele ser en segundos.

4. **Obtener TFO y completados**  

   ```bash
   curl -s "http://localhost:8000/audit/tfo/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
   ```

   La respuesta incluye:
   - `t0`: instante de la solicitud.
   - `completados`: lista con `consumer_id` y `timestamp` por cada consumidor (reader, reservations, analytics).
   - `tfo_seconds`: TFO = max(completados) − T0.
   - `tfo_under_3_min`: `true` si TFO < 180 s (happy path).

5. **Verificar ausencia de PII (evidencias)**  
   Consultar que en todos los sistemas el usuario esté anonimizado:

   ```bash
   # Users (writer)
   docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
     "SELECT id, email, name, anonymized FROM users WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';"

   # Read model
   docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
     "SELECT id, email, name, anonymized FROM user_read_model WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';"

   # Reservations (user_id debe ser el UUID anónimo 00000000-0000-0000-0000-000000000001)
   docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
     "SELECT id, user_id FROM reservations LIMIT 5;"

   # Analytics
   docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
     "SELECT id, user_id, anonymized FROM analytics_user_activity LIMIT 5;"
   ```

   Anotar: en users y user_read_model, email/name anonimizados y `anonymized = true`; en reservas, user_id anónimo; en analytics, `anonymized = true`. El **usuario debe quedar anonimizado** en todos los sistemas: el campo `anonymized` (true/false) indica si ese registro ya fue anonimizado (true = sin PII).

#### Unhappy path 1 — Evento perdido (opcional)

- **Objetivo:** Ver qué pasa si un consumidor no recibe el evento (o RabbitMQ falla) y qué ajustes proponer.
- **Cómo ejecutarlo:**  
  - Opción A: Detener un consumidor antes del POST (ej. `docker stop poc5_gdpr_apoyo_analytics`), disparar derecho al olvido, comprobar TFO y PII (falta completado de analytics). Luego levantar el consumidor y ver si recupera el mensaje (cola persistente) o si se pierde.  
  - Opción B: Simular fallo de RabbitMQ (detener el contenedor un momento, reintentar) y observar si los consumidores recuperan.
- **Qué documentar:** Si se ejecutó: descripción del escenario, resultado (TFO no alcanzado, PII residual en algún sistema), propuesta de ajuste (persistencia de colas, reintentos, dead-letter queue).

#### Unhappy path 2 — Analytics lento (opcional)

- **Objetivo:** Ver el impacto en el TFO cuando un consumidor tarda mucho y qué ajustes proponer.
- **Cómo ejecutarlo:** Añadir un delay artificial en el consumidor de Analytics (ej. `time.sleep(200)` antes de anonimizar) o saturar la cola con muchos mensajes. Levantar entorno, disparar derecho al olvido y medir TFO tras la propagación.
- **Qué documentar:** Si se ejecutó: TFO medido, si hubo PII residual temporalmente, propuesta (timeouts, capacidad de consumidores, monitoreo del TFO).

---

## 2. Información necesaria para terminar el experimento

Recolectar y documentar lo siguiente para el **informe de avance** y la **versión final** del experimento.

### 2.1 Métrica TFO

| Dato | Dónde obtenerlo | Ejemplo |
|------|-----------------|--------|
| T0 | Respuesta de `POST .../derecho-olvido` (campo `t0`) o `GET .../audit/tfo/{user_id}` | `2025-02-28T12:00:00.000Z` |
| T1 (Reader) | `GET .../audit/tfo/{user_id}` → `completados` donde `consumer_id == "reader"` | timestamp |
| T2 (Reservations) | Idem, `consumer_id == "reservations"` | timestamp |
| T3 (Analytics) | Idem, `consumer_id == "analytics"` | timestamp |
| **TFO (segundos)** | `GET .../audit/tfo/{user_id}` → `tfo_seconds` | ej. 2.45 |
| ¿TFO < 3 min? | `tfo_under_3_min` en la misma respuesta | true / false |

**Para que el experimento sea válido, los tres tienen que estar completados (T1, T2 y T3).** Si falta alguno (ej. T3 no aparece en `completados`), la corrida no está completa:

- **Requisito:** En `audit_events` deben figurar 1 `solicitud_olvido` (T0) y 3 `completado` (reader, reservations, analytics). Solo entonces el TFO y la auditoría son válidos para el informe.
- **Si falta T3 (u otro):** No dar por válida la corrida. Revisar que los tres consumidores (core_reader, core_reservations, apoyo_analytics) estén en ejecución antes del POST, que cada uno registre `completado` en `audit_events`, que la cola esté vinculada al exchange (RabbitMQ) y, si aplica, los logs del contenedor (ej. `poc5_gdpr_apoyo_analytics`). El caso de uso de Analytics debe llamar a `record_completado(user_id, consumer_id, timestamp)` con los tres argumentos; sin `timestamp` la escritura en auditoría falla. Corregir código o configuración y **volver a ejecutar** hasta obtener T1, T2 y T3.
- **Cálculo del TFO:** Solo cuando los tres estén en auditoría, `tfo_seconds` = max(T1, T2, T3) − T0. Si en una corrida previa solo había reader y reservations, ese valor es parcial; para el informe final hay que tener los tres completados.

### 2.2 Evidencias antes/después

- **Antes:** captura o anotación de `users`, `user_read_model`, `reservations`, `analytics_user_activity` para el `user_id` de prueba (PII visible).
- **Después:** mismas tablas tras la propagación. El usuario debe estar anonimizado en todos los sistemas: email/name anonimizados, `anonymized = true` en users, user_read_model y analytics; reservas con user_id anónimo.

**Cómo capturar evidencias (pantallazos):** Puedes tomar capturas de pantalla o guardar la salida de los comandos para el informe.

| Evidencia | Dónde obtenerla | Cómo capturarla |
|-----------|-----------------|------------------|
| **Datos en BD (antes/después)** | Salida de los `SELECT` en PostgreSQL | Ejecutar los comandos de sección 1.3 (evidencias ANTES y DESPUÉS) en la terminal; pantallazo del terminal o copiar/pegar la salida en el informe. |
| **Auditoría (audit_events)** | Salida del `SELECT ... FROM audit_events` | `docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT event_type, user_id, consumer_id, timestamp FROM audit_events ORDER BY timestamp;"` — pantallazo o texto de la salida. |
| **TFO y respuesta del API** | Respuesta de `curl` (derecho-olvido y audit/tfo) | Pantallazo del terminal tras `curl -X POST .../derecho-olvido` y `curl .../audit/tfo/{user_id}`; o pegar el JSON en el informe. |
| **Logs de los consumidores** | Docker logs | `docker logs poc5_gdpr_core_reader` (y lo mismo para `poc5_gdpr_core_reservations`, `poc5_gdpr_apoyo_analytics`) — útil si quieres mostrar que procesaron el evento o depurar; pantallazo de las líneas relevantes. |

No hace falta capturar todo: con la salida de la **base de datos** (SELECT antes/después + audit_events) y, si quieres, la respuesta del **API** (TFO), suele bastar para las evidencias del informe.

### 2.3 Registro de auditoría

Para cumplimiento (Historia A5):

```bash
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
  "SELECT event_type, user_id, consumer_id, timestamp FROM audit_events ORDER BY timestamp;"
```

Debe verse: un evento `solicitud_olvido` (T0) y tres eventos `completado` (reader, reservations, analytics).

**Salida (corrida actual):**
```
    event_type    |               user_id                | consumer_id  |         timestamp          
------------------+--------------------------------------+--------------+----------------------------
 solicitud_olvido | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 |              | 2026-03-01 20:07:34.694813
 completado       | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | analytics    | 2026-03-01 20:07:34.730721
 completado       | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | reservations | 2026-03-01 20:07:34.730868
 completado       | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | reader       | 2026-03-01 20:07:34.731174
(4 rows)
```

### 2.4 Casos ejecutados

**Los unhappy paths deben documentarse siempre.** Si no sucedieron, hay que **explicar por qué**: no ocurren por sí solos en una corrida normal; solo aparecen si se reproducen a propósito (detener un consumidor, añadir delay, etc.). En la tabla: estado "No ejecutado" y razón breve, p. ej. "No se provocaron en esta corrida; solo se ejecutó el flujo normal (happy path)." No dejar la celda en blanco.

| Caso | Cómo ejecutarlo | Qué documentar |
|------|-----------------|----------------|
| **Happy path** | Flujo de la sección 1.3 con usuario de prueba | TFO en segundos, desglose por consumidor, capturas de ausencia de PII en los 4 sistemas. |
| **Unhappy 1** (evento perdido) | Opcional: detener un consumidor antes del POST, luego levantar y ver si recupera; o simular fallo de RabbitMQ. | Si ejecutado: descripción, resultado (TFO no alcanzado o PII residual), propuesta (persistencia, reintentos, DLQ). **Si no ejecutado:** "No ejecutado" + razón breve (ej. no se reprodujeron en esta corrida). |
| **Unhappy 2** (Analytics lento) | Opcional: añadir delay en el consumidor de Analytics o saturar la cola. | Si ejecutado: TFO medido, PII residual si la hay, propuesta (timeouts, capacidad, monitoreo). **Si no ejecutado:** "No ejecutado" + razón breve. |

---

## 3. Resultados (informe final)

Resultados de la corrida ejecutada el 2026-03-01 con `./scripts/ejecutar_experimento_desde_cero.sh`. Usuario de prueba: `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11`.

### 3.1 Métrica TFO (resumen)

| Dato | Valor |
|------|--------|
| T0 (solicitud aceptada) | 2026-03-01T20:07:34.694813Z |
| T1 (Reader completado) | 2026-03-01T20:07:34.731174 |
| T2 (Reservations completado) | 2026-03-01T20:07:34.730868 |
| T3 (Analytics completado) | 2026-03-01T20:07:34.730721 |
| **TFO (segundos)** | 0.04 |
| Meta TFO < 3 min | **Sí** |

### 3.2 Evidencias antes / después

| Sistema | Antes (PII visible) | Después (anonimizado) |
|---------|---------------------|------------------------|
| User Service (users) | email: test@travelhub.com, name: Test User, anonymized=false | anon_a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11@deleted.local, DELETED, true |
| Reader (user_read_model) | email: test@travelhub.com, name: Test User, anonymized=false | anon_a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11@deleted.local, DELETED, true |
| Reservations | user_id = a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | user_id = 00000000-0000-0000-0000-000000000001 |
| Analytics | user_id presente, anonymized=false | anonymized=true |

Integridad referencial en reservas: reservas conservadas con user_id anonimizado. **Sí**

### 3.3 Registro de auditoría

| event_type | consumer_id | timestamp |
|------------|-------------|-----------|
| solicitud_olvido | — | 2026-03-01 20:07:34.694813 |
| completado | analytics | 2026-03-01 20:07:34.730721 |
| completado | reservations | 2026-03-01 20:07:34.730868 |
| completado | reader | 2026-03-01 20:07:34.731174 |

*Nota:* `solicitud_olvido` no tiene `consumer_id` porque lo registra el **origen** del flujo (User Service), no un consumidor de la cola; `consumer_id` solo aplica a los eventos `completado` de cada consumidor (reader, reservations, analytics).

**Salida de `SELECT event_type, consumer_id, timestamp FROM audit_events ORDER BY timestamp`:**
```
    event_type    |               user_id                | consumer_id  |         timestamp          
------------------+--------------------------------------+--------------+----------------------------
 solicitud_olvido | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 |              | 2026-03-01 20:07:34.694813
 completado       | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | analytics    | 2026-03-01 20:07:34.730721
 completado       | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | reservations | 2026-03-01 20:07:34.730868
 completado       | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | reader       | 2026-03-01 20:07:34.731174
(4 rows)
```

### 3.4 Casos ejecutados

| Caso | Estado | Descripción / TFO / ajustes |
|------|--------|-----------------------------|
| Happy path | **Completado** | TFO 0.04 s; PII eliminado en users, user_read_model, reservations y analytics. Meta TFO &lt; 3 min cumplida. |
| Unhappy 1 (evento perdido) | **Ejecutado** | Se detuvo el consumidor Analytics antes del POST. Resultado: solo 2 completados (reader, reservations), TFO parcial 0.05 s; **PII residual en Analytics** (anonymized=false). Al levantar Analytics de nuevo, el mensaje estaba en la cola (RabbitMQ persistente): procesó y registró completado; TFO final 70.4 s (&lt; 3 min). **Ajuste:** colas duraderas, reintentos y DLQ ya ayudan; monitorear consumidores caídos. |
| Unhappy 2 (Analytics lento) | **Ejecutado** | Se añadió delay de 15 s en el consumidor Analytics (env `DELAY_ANALYTICS_SEC=15`). TFO medido: **15.04 s**; meta &lt; 3 min cumplida. Los tres completados; sin PII residual. **Ajuste:** timeouts por consumidor, capacidad y monitoreo del TFO en producción. |

### 3.5 Unhappy paths ejecutados (detalle)

**Unhappy 1 — Evento “perdido” (consumidor caído):**
- **Escenario:** Entorno reiniciado (datos frescos). Se detuvo `poc5_gdpr_apoyo_analytics` antes de `POST /derecho-olvido`. Se disparó el derecho al olvido (T0: 2026-03-01T20:17:30.978418Z).
- **Resultado inmediato:** Solo 2 completados en auditoría (reader, reservations). TFO reportado 0.05 s (parcial). En `analytics_user_activity`: **anonymized = false** (PII residual en Analytics).
- **Tras levantar Analytics:** El consumidor se reconectó a RabbitMQ; el mensaje seguía en la cola (exchange/cola duraderos). Analytics procesó el evento y registró `completado` a las 20:18:41. TFO final 70.4 s; `analytics_user_activity.anonymized = true`. No hubo pérdida real del evento.
- **Ajustes propuestos:** Mantener colas y mensajes persistentes; reintentos en consumidores; dead-letter queue para fallos definitivos; alertas cuando un consumidor no registra completado en un tiempo acotado.

**Unhappy 2 — Analytics lento:**
- **Escenario:** Variable de entorno `DELAY_ANALYTICS_SEC=15` en el consumidor Analytics; al recibir el evento hace `time.sleep(15)` antes de anonimizar. Entorno reiniciado, POST derecho-olvido (T0: 2026-03-01T20:20:30.615896Z).
- **Resultado:** Reader y Reservations completaron en &lt; 0.05 s; Analytics completó a los ~15 s. TFO = **15.04 s** (dominado por el delay). Meta &lt; 3 min cumplida. Los tres sistemas anonimizados; sin PII residual.
- **Ajustes propuestos:** En producción: timeouts por consumidor, escalado o más instancias si un consumidor es cuello de botella, y monitoreo del TFO (alertas si TFO se acerca a 3 min).

### 3.6 Conclusiones de los unhappy paths

**Unhappy 1 (evento perdido / consumidor caído):**
- **Conclusión:** Un consumidor caído no implica pérdida del evento si el broker usa colas y mensajes persistentes. En el experimento, el mensaje permaneció en RabbitMQ; al volver a levantar Analytics, se procesó y se anonimizó el dato, con TFO final 70.4 s (< 3 min). Durante el tiempo en que el consumidor estuvo caído hubo **PII residual temporal** en Analytics; la auditoría reflejó solo 2 completados hasta que Analytics registró el suyo. Para cumplimiento, es importante **monitorear que los tres consumidores registren "completado"** y alertar si uno no lo hace en un tiempo acotado.
- **Recomendación:** Mantener colas duraderas, reintentos en consumidores y una dead-letter queue para mensajes que fallen de forma definitiva; así se reduce el riesgo de PII residual prolongado.

**Unhappy 2 (Analytics lento):**
- **Conclusión:** Un consumidor lento determina el TFO. Con un delay de 15 s en Analytics, el TFO fue 15.04 s; la meta de 3 minutos se siguió cumpliendo. No hubo PII residual: los tres sistemas quedaron anonimizados, solo que el último completado (Analytics) llegó más tarde. El diseño es **tolerante a un consumidor lento** siempre que complete dentro del límite (p. ej. 3 min).
- **Recomendación:** En producción, vigilar el TFO y la carga de cada consumidor; si uno se convierte en cuello de botella, escalar o ajustar capacidad para que el TFO se mantenga bajo 3 min.

**Resumen:** Los dos unhappy paths **refuerzan el diseño** y **en ambos se cumple la meta TFO &lt; 3 min**: Unhappy 1 con TFO final 70.4 s (una vez Analytics se recuperó y completó) y Unhappy 2 con TFO 15.04 s. El TFO es el tiempo hasta que el último consumidor registra "completado"; por eso, aunque haya fallo o lentitud, si los tres terminan antes de 3 minutos el criterio se cumple. La cola persistente permite recuperación (Unhappy 1) y el TFO refleja correctamente al consumidor más lento (Unhappy 2). Las mejoras propuestas (persistencia, reintentos, DLQ, monitoreo) son recomendaciones operativas para producción, no cambios de arquitectura.

---

## 4. Conclusiones (informe final)

Conclusiones según el resultado del experimento (corrida 2026-03-01).

### 4.1 Validación de la hipótesis

| Criterio | Cumple | Comentario |
|----------|--------|------------|
| TFO < 3 minutos | **Sí** | TFO medido: 0.04 s (meta: < 180 s). Fuente: `GET /audit/tfo/{user_id}` → `tfo_seconds`. |
| Ausencia de PII en User Service, Reader, Reservas y Analytics | **Sí** | El usuario quedó anonimizado en los cuatro sistemas: email/name anonimizados y `anonymized = true` en users y user_read_model; user_id anónimo en reservas; `anonymized = true` en analytics (tabla sección 3.2). |
| Integridad referencial en reservas (reservas conservadas, usuario anonimizado) | **Sí** | Las reservas no se eliminaron; el `user_id` pasó al UUID anónimo fijo 00000000-0000-0000-0000-000000000001. |
| Registro de auditoría (T0 + completado por consumidor) | **Sí** | En `audit_events`: 1 fila `solicitud_olvido` (T0) y 3 filas `completado` (reader, reservations, analytics). Base para TFO y trazabilidad. |

**Conclusión sobre la hipótesis:** [X] Se **valida** la hipótesis H1: la propagación distribuida por eventos y el diseño permiten cumplir el derecho al olvido en tiempo acotado y medible (TFO 0.04 s, ausencia de PII en los cuatro sistemas, auditoría completa).

### 4.2 Cumplimiento de requisitos (Historia A5 y Semana 2)

- **Derecho al olvido:** **Cumplido.** En este PoC se cumple mediante **anonimización** (no eliminación de filas): los datos personales dejan de identificar al usuario en User Service, Reader, Reservations y Analytics.
- **Auditoría:** **Cumplido.** Existe registro de la solicitud de olvido (T0) y de la confirmación por cada consumidor (reader, reservations, analytics) para trazabilidad y medición del TFO.

### 4.3 Limitaciones y mejoras (si aplica)

- **Limitaciones observadas:** En Unhappy 1, con un consumidor caído hubo PII residual temporal en Analytics hasta que el consumidor se levantó y procesó el mensaje de la cola. En Unhappy 2, un consumidor lento (15 s) elevó el TFO a 15.04 s; la meta &lt; 3 min se mantuvo. El entorno es local y no representa carga real en producción.
- **Ajustes realizados o propuestos:** (1) **Broker:** colas y mensajes persistentes (ya en uso); dead-letter queue y reintentos para mensajes fallidos. (2) **Consumidores:** reintentos, timeouts y monitoreo de “completado” por consumidor. (3) **TFO:** alertas si TFO se acerca a 3 min o si falta algún completado (p. ej. Analytics caído).
- **Ajustes a la arquitectura:** No se cambiaron modelos; los unhappy paths validaron que la cola persistente permite recuperación (Unhappy 1) y que el TFO refleja al consumidor más lento (Unhappy 2). El consumidor de Analytics admite `DELAY_ANALYTICS_SEC` (env) para reproducir Unhappy 2; en operación normal debe ser 0.

### 4.4 Contenido completo para el informe final

Incluido en este documento:

1. **Métrica TFO:** 0.04 s; T0: 2026-03-01T20:07:34.694813Z; T1 (reader), T2 (reservations), T3 (analytics) en sección 3.1; TFO < 3 min: sí.
2. **Tabla de criterios de validación:** sección 4.1 (cuatro criterios con Cumple Sí y comentario).
3. **Conclusión explícita:** sección 4.1 — se valida la hipótesis H1; el diseño cumple derecho al olvido y auditoría (Historia A5).
4. **Evidencias antes/después:** sección 3.2 (users, user_read_model, reservations, analytics).
5. **Registro de auditoría:** sección 3.3 (tabla y salida de `audit_events`).
6. **Casos ejecutados:** sección 3.4 (Happy path completado; Unhappy 1 y 2 **ejecutados** con resultados y ajustes).
7. **Unhappy paths ejecutados:** sección 3.5 (detalle); **Conclusiones de los unhappy paths:** sección 3.6 (conclusiones y recomendaciones por escenario).
8. **Limitaciones y mejoras:** sección 4.3 (broker, consumidores, monitoreo TFO).

---

## 5. Checklist para cerrar el experimento

- [ ] Entorno levantado con `docker compose up -d` y **los seis** contenedores en running (db, rabbitmq, core_user_service, core_reader, core_reservations, **apoyo_analytics**). Sin Analytics levantado el experimento no es válido.
- [ ] Ejecutado al menos un happy path con el usuario de prueba.
- [ ] Anotado T0 y TFO (y, si aplica, T1, T2, T3).
- [ ] Verificada ausencia de PII en users, user_read_model, reservations, analytics_user_activity.
- [ ] Consultado `audit_events` y documentado (solicitud_olvido + 3 completado).
- [ ] Resultados redactados (TFO, evidencias, casos happy/unhappy).
- [ ] Conclusiones redactadas (validación o refutación de la hipótesis, ajustes si aplica).
- [ ] Ajustes a la arquitectura (si los hubo por unhappy paths) documentados por escrito y en el video, según indicación del curso.

---

## 6. Referencia rápida (comandos de la prueba)

Todos los comandos ejecutados durante la prueba, en orden. Usuario de prueba: `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11`.

**Correr todo el experimento desde cero (recomendado; incluye T1, T2, T3):**
```bash
cd poc5-gdpr
./scripts/ejecutar_experimento_desde_cero.sh
# Abre EXPERIMENTO_SALIDA.txt y copia los bloques al informe (Anexo A y B)
```

**Comandos paso a paso (manual):**
```bash
# --- Levantar entorno (o desde cero: docker compose down -v antes) ---
cd poc5-gdpr
docker compose up -d

# (Opcional) Reset completo: datos frescos (borra BD)
# docker compose down -v
# docker compose up -d
# Esperar ~30 s a que init.sql cree el usuario y los consumidores conecten

# --- Comprobar estado y salud ---
docker compose ps
curl -s http://localhost:8000/health

# --- Evidencias ANTES (estado con PII) ---
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
  "SELECT id, email, name, anonymized FROM users WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';"
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
  "SELECT id, email, name, anonymized FROM user_read_model WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';"
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
  "SELECT id, user_id FROM reservations LIMIT 5;"
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
  "SELECT id, user_id, anonymized FROM analytics_user_activity LIMIT 5;"

# --- Disparar derecho al olvido (T0 se registra aquí) ---
curl -s -X POST "http://localhost:8000/users/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/derecho-olvido"

# --- TFO y completados ---
curl -s "http://localhost:8000/audit/tfo/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

# --- Evidencias DESPUÉS (anonimizado) ---
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
  "SELECT id, email, name, anonymized FROM users WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';"
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
  "SELECT id, email, name, anonymized FROM user_read_model WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';"
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
  "SELECT id, user_id FROM reservations LIMIT 5;"
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
  "SELECT id, user_id, anonymized FROM analytics_user_activity LIMIT 5;"

# --- Auditoría (tabla audit_events) ---
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c \
  "SELECT event_type, user_id, consumer_id, timestamp FROM audit_events ORDER BY timestamp;"

# --- Bajar entorno ---
docker compose down
```

---

## Anexo A. Evidencias capturadas (salida de comandos)

Salida real de los comandos de evidencia ejecutados en el entorno. Puedes usar este bloque como “pantallazos” en texto para el informe (o re-ejecutar y sustituir por una corrida nueva).

**Health (User Service):**
```
{"status":"ok"}
```

**Users (usuario de prueba — estado tras derecho al olvido):**
```
                  id                  |                          email                          |  name   | anonymized 
--------------------------------------+---------------------------------------------------------+---------+------------
 a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | anon_a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11@deleted.local | DELETED | t
(1 row)
```

**User read model (Reader):**
```
                  id                  |                          email                          |  name   | anonymized 
--------------------------------------+---------------------------------------------------------+---------+------------
 a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | anon_a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11@deleted.local | DELETED | t
(1 row)
```

**Reservations (user_id anónimo):**
```
                  id                  |               user_id                
--------------------------------------+--------------------------------------
 f4a74489-696b-4caa-b6ba-941e6df1156d | 00000000-0000-0000-0000-000000000001
(1 row)
```

**Analytics (analytics_user_activity):**
```
                  id                  |               user_id                | anonymized 
--------------------------------------+--------------------------------------+------------
 31737998-0c54-48cd-8a61-164846bb44b5 | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | t
(1 row)
```

**Auditoría (audit_events):**
```
    event_type    |               user_id                | consumer_id  |         timestamp          
------------------+--------------------------------------+--------------+----------------------------
 solicitud_olvido | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 |              | 2026-03-01 20:07:34.694813
 completado       | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | analytics    | 2026-03-01 20:07:34.730721
 completado       | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | reservations | 2026-03-01 20:07:34.730868
 completado       | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | reader       | 2026-03-01 20:07:34.731174
(4 rows)
```

**API TFO (`GET /audit/tfo/{user_id}`):**
```json
{"user_id":"a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11","t0":"2026-03-01T20:07:34.694813","completados":[{"consumer_id":"analytics","timestamp":"2026-03-01T20:07:34.730721"},{"consumer_id":"reservations","timestamp":"2026-03-01T20:07:34.730868"},{"consumer_id":"reader","timestamp":"2026-03-01T20:07:34.731174"}],"tfo_seconds":0.04,"tfo_under_3_min":true}
```

*Corrida nueva: 2026-03-01. Los tres consumidores (reader, reservations, analytics) registraron "completado" en `audit_events`. TFO 0.04 s; meta &lt; 3 min cumplida.*

### Anexo B. Logs y resultados (completo)

Todo en un solo anexo: resultados (evidencias de BD y API) y logs de los servicios. Comandos de referencia al final.

---

#### B.1 Resultados (evidencias)

**Health (User Service)** — `curl -s http://localhost:8000/health`
```
{"status":"ok"}
```

**Users (usuario de prueba)** — `docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, email, name, anonymized FROM users WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';"`
```
                  id                  |                          email                          |  name   | anonymized 
--------------------------------------+---------------------------------------------------------+---------+------------
 a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | anon_a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11@deleted.local | DELETED | t
(1 row)
```

**User read model (Reader)** — `docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, email, name, anonymized FROM user_read_model WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';"`
```
                  id                  |                          email                          |  name   | anonymized 
--------------------------------------+---------------------------------------------------------+---------+------------
 a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | anon_a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11@deleted.local | DELETED | t
(1 row)
```

**Reservations** — `docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, user_id FROM reservations LIMIT 5;"`
```
                  id                  |               user_id                
--------------------------------------+--------------------------------------
 f4a74489-696b-4caa-b6ba-941e6df1156d | 00000000-0000-0000-0000-000000000001
(1 row)
```

**Analytics (analytics_user_activity)** — `docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, user_id, anonymized FROM analytics_user_activity LIMIT 5;"`
```
                  id                  |               user_id                | anonymized 
--------------------------------------+--------------------------------------+------------
 31737998-0c54-48cd-8a61-164846bb44b5 | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | t
(1 row)
```

**Auditoría (audit_events)** — `docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT event_type, user_id, consumer_id, timestamp FROM audit_events ORDER BY timestamp;"`
```
    event_type    |               user_id                | consumer_id  |         timestamp          
------------------+--------------------------------------+--------------+----------------------------
 solicitud_olvido | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 |              | 2026-03-01 20:07:34.694813
 completado       | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | analytics    | 2026-03-01 20:07:34.730721
 completado       | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | reservations | 2026-03-01 20:07:34.730868
 completado       | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | reader       | 2026-03-01 20:07:34.731174
(4 rows)
```

**API TFO** — `curl -s "http://localhost:8000/audit/tfo/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"`
```json
{"user_id":"a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11","t0":"2026-03-01T20:07:34.694813","completados":[{"consumer_id":"analytics","timestamp":"2026-03-01T20:07:34.730721"},{"consumer_id":"reservations","timestamp":"2026-03-01T20:07:34.730868"},{"consumer_id":"reader","timestamp":"2026-03-01T20:07:34.731174"}],"tfo_seconds":0.04,"tfo_under_3_min":true}
```

**Resultados completos (sin resumir):**

| Dato | Valor |
|------|--------|
| T0 (solicitud aceptada) | 2026-03-01T20:07:34.694813Z |
| T1 (Reader completado) | 2026-03-01T20:07:34.731174 |
| T2 (Reservations completado) | 2026-03-01T20:07:34.730868 |
| T3 (Analytics completado) | 2026-03-01T20:07:34.730721 |
| TFO (segundos) | 0.04 |
| tfo_under_3_min | true |
| user_id | a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 |

Completados (lista completa de la respuesta del API):
- consumer_id: analytics, timestamp: 2026-03-01T20:07:34.730721
- consumer_id: reservations, timestamp: 2026-03-01T20:07:34.730868
- consumer_id: reader, timestamp: 2026-03-01T20:07:34.731174

Estado de cada sistema tras derecho al olvido:
- **users:** id a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11, email anon_a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11@deleted.local, name DELETED, anonymized true
- **user_read_model:** id a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11, email anon_a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11@deleted.local, name DELETED, anonymized true
- **reservations:** al menos una fila con user_id 00000000-0000-0000-0000-000000000001 (id f4a74489-696b-4caa-b6ba-941e6df1156d)
- **analytics_user_activity:** al menos una fila con anonymized true (id 31737998-0c54-48cd-8a61-164846bb44b5)

Respuesta completa del API (GET /audit/tfo/{user_id}):  
`{"user_id":"a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11","t0":"2026-03-01T20:07:34.694813","completados":[{"consumer_id":"analytics","timestamp":"2026-03-01T20:07:34.730721"},{"consumer_id":"reservations","timestamp":"2026-03-01T20:07:34.730868"},{"consumer_id":"reader","timestamp":"2026-03-01T20:07:34.731174"}],"tfo_seconds":0.04,"tfo_under_3_min":true}`

---

#### B.2 Logs de los servicios

**Core User Service** — `docker logs poc5_gdpr_core_user_service 2>&1 | tail -80`
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     192.168.65.1:37838 - "GET /health HTTP/1.1" 200 OK
INFO:     192.168.65.1:41988 - "POST /users/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/derecho-olvido HTTP/1.1" 200 OK
INFO:     192.168.65.1:52530 - "GET /audit/tfo/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 HTTP/1.1" 200 OK
```
Línea a línea: Started server process [1]; Waiting for application startup; Application startup complete; Uvicorn running on http://0.0.0.0:8000; GET /health → 200 OK; POST /users/.../derecho-olvido → 200 OK (solicitud aceptada, T0 registrado); GET /audit/tfo/... → 200 OK.

**Core Reader** — `docker logs poc5_gdpr_core_reader 2>&1 | tail -50`
```
Connecting to RabbitMQ...
Subscribed to queue reader_usuario_olvidado
Received UsuarioOlvidado user_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11
Anonymized user in read model; recorded completado in audit_events
```
*Evidencia: audit_events (completado, reader) y user_read_model anonimizado.*

**Core Reservations** — `docker logs poc5_gdpr_core_reservations 2>&1 | tail -50`
```
Connecting to RabbitMQ...
Subscribed to queue reservations_usuario_olvidado
Received UsuarioOlvidado user_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11
Updated reservations with anonymous user_id; recorded completado in audit_events
```
*Evidencia: audit_events (completado, reservations) y reservations.user_id anónimo.*

**Apoyo Analytics** — `docker logs poc5_gdpr_apoyo_analytics 2>&1 | tail -50`
```
Connecting to RabbitMQ...
Subscribed to queue analytics_usuario_olvidado
Received UsuarioOlvidado user_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11
Anonymized analytics_user_activity; recorded completado in audit_events
```
*Evidencia: audit_events (completado, analytics) y analytics_user_activity.anonymized = true. Los tres consumidores completaron en esta corrida.*

**Reconstruir todo y reiniciar para ver los logs:** en tu máquina, desde la carpeta `poc5-gdpr`, ejecuta un solo comando:

```bash
cd poc5-gdpr
./scripts/reconstruir_y_ver_logs.sh
```

El script hace: `docker compose down` → `docker compose build --no-cache` de los tres consumidores → `docker compose up -d` → espera 15 s → dispara el derecho al olvido → imprime los logs de Reader, Reservations y Analytics. Si quieres datos frescos antes, ejecuta primero `docker compose down -v` y luego `./scripts/reconstruir_y_ver_logs.sh` (edita el script y quita el `down` del inicio si ya hiciste `down -v`).

**Comandos a mano (si prefieres):**
```bash
cd poc5-gdpr
docker compose down
docker compose build --no-cache core-reader-service core-reservations-consumer apoyo-analytics-consumer
docker compose up -d
sleep 15
curl -s -X POST "http://localhost:8000/users/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/derecho-olvido"
docker logs poc5_gdpr_core_reader 2>&1 | tail -50
docker logs poc5_gdpr_core_reservations 2>&1 | tail -50
docker logs poc5_gdpr_apoyo_analytics 2>&1 | tail -50
```

---

---

## 7. Resultados de la ejecución (corrida 2026-03-01)

*Corrida con el stack en Docker (ejecutada con `./scripts/ejecutar_experimento_desde_cero.sh`). Usuario de prueba: `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11`.*

### 7.1 Métrica TFO

| Dato | Valor |
|------|--------|
| T0 (solicitud aceptada) | 2026-03-01T20:07:34.694813Z |
| T1 (Reader completado) | 2026-03-01T20:07:34.731174 |
| T2 (Reservations completado) | 2026-03-01T20:07:34.730868 |
| T3 (Analytics completado) | 2026-03-01T20:07:34.730721 |
| **TFO (segundos)** | 0.04 |
| Meta TFO < 3 min | **Sí** |

*Corrida 2026-03-01: los tres consumidores (reader, reservations, analytics) registraron "completado" en `audit_events`. TFO = max(T1, T2, T3) − T0.*

### 7.2 Evidencias: estado antes / después

| Sistema | Antes (PII visible) | Después (anonimizado) |
|---------|----------------------|------------------------|
| User Service (users) | email: test@travelhub.com, name: Test User, anonymized: false | email: anon_...@deleted.local, name: DELETED, anonymized: true |
| Reader (user_read_model) | email: test@travelhub.com, name: Test User, anonymized: false | email: anon_...@deleted.local, name: DELETED, anonymized: true |
| Reservations | user_id: a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 | user_id: 00000000-0000-0000-0000-000000000001 |
| Analytics (analytics_user_activity) | user_id presente, anonymized: false | anonymized: true |

*En todos los sistemas el usuario debe quedar anonimizado tras el derecho al olvido; `anonymized: true` indica que ese registro ya fue anonimizado (sin PII).*

**Integridad referencial en reservas:** Sí — reservas conservadas con user_id anonimizado (UUID fijo).

### 7.3 Registro de auditoría

| event_type | consumer_id | timestamp |
|------------|-------------|-----------|
| solicitud_olvido | — | 2026-03-01 20:07:34.694813 |
| completado | analytics | 2026-03-01 20:07:34.730721 |
| completado | reservations | 2026-03-01 20:07:34.730868 |
| completado | reader | 2026-03-01 20:07:34.731174 |

*Nota:* `solicitud_olvido` tiene `consumer_id` en blanco (—) porque lo registra el **origen** del flujo (User Service), no un consumidor; `consumer_id` solo se rellena en los eventos `completado` de cada consumidor.

### 7.4 Casos ejecutados

| Caso | Estado | Descripción |
|------|--------|-------------|
| Happy path | Completado | TFO 0.04 s; PII eliminado en users, user_read_model, reservations y analytics. Meta TFO < 3 min cumplida. |
| Unhappy 1 (evento perdido) | **Ejecutado** | Se detuvo Analytics antes del POST. Solo 2 completados; PII residual en Analytics (anonymized=false). Al levantar Analytics, procesó el mensaje de la cola; TFO final 70.4 s. Colas persistentes permiten recuperación. |
| Unhappy 2 (Analytics lento) | **Ejecutado** | Delay 15 s en Analytics (`DELAY_ANALYTICS_SEC=15`). TFO 15.04 s; meta < 3 min cumplida. Sin PII residual. TFO dominado por el consumidor más lento. |

**Detalle y conclusiones de los unhappy paths:** Ver sección 3.5 (detalle de escenarios y resultados) y **sección 3.6 (conclusiones por unhappy path)**. Se reprodujeron a propósito: Unhappy 1 deteniendo el consumidor Analytics antes del POST; Unhappy 2 con delay de 15 s en Analytics. Conclusiones: cola persistente permite recuperación (Unhappy 1); TFO refleja al consumidor más lento (Unhappy 2). Ajustes en sección 4.3.

### 7.5 Conclusiones de la corrida

Las conclusiones se organizan por tipo de caso: **Happy path** (flujo normal) y **Unhappy paths** (evento perdido y consumidor lento).

---

#### Por caso: Happy path (flujo normal)

**Validación de la hipótesis**

| Criterio | Cumple | Comentario |
|----------|--------|-------------|
| TFO < 3 minutos | **Sí** | TFO medido: 0.04 s. |
| Ausencia de PII en los cuatro sistemas | **Sí** | Users, user_read_model, reservations y analytics anonimizados. |
| Integridad referencial en reservas | **Sí** | Reservas conservadas con user_id anónimo (UUID fijo). |
| Registro de auditoría (T0 + completado) | **Sí** | T0 registrado; reader, reservations y analytics registran "completado" en auditoría; trazabilidad y TFO medibles. |

**Conclusión Happy path:** Se **valida** la hipótesis H1: la propagación distribuida por eventos permite cumplir el derecho al olvido en tiempo acotado (TFO 0.04 s) y con ausencia de PII en todos los sistemas. La trazabilidad mediante auditoría queda completada: T0 y los tres consumidores (Reader, Reservations, Analytics) registran en `audit_events`.

**Cumplimiento de requisitos (Historia A5)**

- **Derecho al olvido:** Cumplido. Los datos personales del usuario se anonimizaron en el writer (User Service) y en los tres consumidores (Reader, Reservations, Analytics).
- **Auditoría:** Cumplido. Existe registro de la solicitud (T0) y de la confirmación por parte de Reader, Reservations y Analytics; trazabilidad y TFO medibles.

---

#### Por caso: Unhappy paths

**Por qué los unhappy paths también cumplen el TFO (< 3 min):** El TFO se mide desde T0 hasta el instante en que el **último** de los tres consumidores (reader, reservations, analytics) registra "completado" en auditoría. Es decir, el derecho al olvido se considera cumplido en tiempo cuando los cuatro sistemas (User Service + los tres consumidores) han anonimizado al usuario. En **Unhappy 1**, tras levantar Analytics este procesó el mensaje de la cola y registró completado a los 70.4 s de T0 → TFO final 70.4 s, que es **menor que 180 s (3 min)**. En **Unhappy 2**, los tres consumidores completaron; el más lento (Analytics con delay de 15 s) fijó el TFO en 15.04 s, también **menor que 3 min**. Por tanto, en ambos escenarios la meta de TFO se cumple; la diferencia es que en Unhappy 1 hubo PII residual temporal hasta que Analytics se recuperó, y en Unhappy 2 el TFO es mayor que en el happy path pero sigue dentro del límite.

**Unhappy 1 (evento perdido / consumidor caído)**

- **Qué se hizo:** Se detuvo el consumidor Analytics antes del POST derecho-olvido.
- **Resultado:** Solo 2 completados al inicio; PII residual temporal en Analytics. Al levantar Analytics, el mensaje seguía en la cola; se procesó y se anonimizó; TFO final 70.4 s (< 3 min).
- **Conclusión:** La cola persistente **evita la pérdida del evento**; hay recuperación cuando el consumidor vuelve. Es importante monitorear que los tres consumidores registren "completado" y alertar si falta alguno.
- **Recomendación:** Mantener colas duraderas, reintentos y dead-letter queue.

**Unhappy 2 (Analytics lento)**

- **Qué se hizo:** Se añadió un delay de 15 s en el consumidor Analytics (`DELAY_ANALYTICS_SEC=15`).
- **Resultado:** TFO 15.04 s (dominado por Analytics); meta < 3 min cumplida; sin PII residual.
- **Conclusión:** El TFO lo define el **consumidor más lento**; el diseño tolera un consumidor lento siempre que complete dentro del límite (p. ej. 3 min).
- **Recomendación:** Monitorear TFO y carga de consumidores; escalar o ajustar capacidad si uno se convierte en cuello de botella.

**Resumen Unhappy paths:** Ambos escenarios **refuerzan el diseño**: recuperación vía cola (Unhappy 1) y TFO correcto (Unhappy 2). Limitaciones: PII residual temporal en Unhappy 1 hasta recuperación; TFO mayor en Unhappy 2. Mejoras propuestas: persistencia, reintentos, DLQ, monitoreo de consumidores y TFO (detalle en sección 4.3). Para reproducir Unhappy 2: `DELAY_ANALYTICS_SEC=15` en el consumidor Analytics; en operación normal usar 0.

---

#### Contenido completo para el informe final (esta corrida)

- **TFO:** Happy path 0.04 s. Unhappy 1: TFO parcial 0.05 s (2 completados), TFO final 70.4 s tras levantar Analytics. Unhappy 2: TFO 15.04 s (delay 15 s en Analytics). Meta < 3 min cumplida en todos los casos.
- **Diseño:** Validado para el derecho al olvido y la auditoría en red distribuida (Historia A5). Los unhappy paths ejecutados confirman recuperación vía cola (Unhappy 1) y que el TFO refleja al consumidor más lento (Unhappy 2).
- **Evidencias:** Tabla 7.1; tabla 7.2; tabla 7.3; tabla 7.4 (Happy path + Unhappy 1 y 2 **ejecutados** con resultados). sección 3.5 detalle de ambos unhappy paths.
- **Casos:** Happy path completado (TFO 0.04 s). Unhappy 1 ejecutado: consumidor Analytics detenido → PII residual temporal → al levantar Analytics, mensaje en cola procesado, TFO final 70.4 s. Unhappy 2 ejecutado: delay 15 s en Analytics → TFO 15.04 s, sin PII residual.
- **Limitaciones y mejoras:** sección 4.3 (broker, consumidores, monitoreo TFO). Variable `DELAY_ANALYTICS_SEC` en Analytics para reproducir consumidor lento; en producción debe ser 0.

---

*Documento alineado al diseño del experimento en la wiki (Experimento-derecho-olvido) y a la implementación en `poc5-gdpr`.*
