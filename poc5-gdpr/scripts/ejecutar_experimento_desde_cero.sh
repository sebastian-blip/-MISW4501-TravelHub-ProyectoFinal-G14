#!/usr/bin/env bash
# Ejecuta todo el experimento desde cero: borra volúmenes, levanta los seis
# contenedores (incluido Analytics), espera a init.sql y consumidores, dispara
# derecho al olvido y captura toda la salida en EXPERIMENTO_SALIDA.txt.
# Uso: cd poc5-gdpr && ./scripts/ejecutar_experimento_desde_cero.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="${OUT:-$ROOT/EXPERIMENTO_SALIDA.txt}"
USER_ID="${USER_ID:-a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11}"

echo "=== Experimento desde cero (down -v, up -d, POST, captura) ==="
echo "Salida en: $OUT"
echo ""

exec > "$OUT" 2>&1
echo "=== $(date -Iseconds 2>/dev/null || date) ==="
echo ""

echo "=== 1. Docker compose down -v (borrar volúmenes, estado inicial) ==="
docker compose down -v
echo ""

echo "=== 2. Docker compose up -d (los seis contenedores, incluido apoyo_analytics) ==="
docker compose up -d
echo ""

echo "=== 3. Esperando 30 s (init.sql crea usuario de prueba; RabbitMQ y consumidores arrancan) ==="
sleep 30
echo ""

echo "=== 4. Estado de contenedores (deben aparecer los seis) ==="
docker compose ps
echo ""

echo "=== 5. Health ==="
curl -s http://localhost:8000/health || echo "(fallo)"
echo ""
echo ""

echo "=== 6. POST derecho-olvido (T0 se registra aquí) ==="
curl -s -X POST "http://localhost:8000/users/${USER_ID}/derecho-olvido" || echo "(fallo)"
echo ""
echo ""

echo "=== 7. Esperando 10 s a que los tres consumidores procesen ==="
sleep 10
echo ""

echo "=== 8. Users ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, email, name, anonymized FROM users WHERE id = '${USER_ID}';" 2>/dev/null || echo "(fallo)"
echo ""

echo "=== 9. User read model ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, email, name, anonymized FROM user_read_model WHERE id = '${USER_ID}';" 2>/dev/null || echo "(fallo)"
echo ""

echo "=== 10. Reservations ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, user_id FROM reservations LIMIT 5;" 2>/dev/null || echo "(fallo)"
echo ""

echo "=== 11. Analytics ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, user_id, anonymized FROM analytics_user_activity LIMIT 5;" 2>/dev/null || echo "(fallo)"
echo ""

echo "=== 12. Audit events (debe haber 1 solicitud_olvido + 3 completado: reader, reservations, analytics) ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT event_type, user_id, consumer_id, timestamp FROM audit_events ORDER BY timestamp;" 2>/dev/null || echo "(fallo)"
echo ""

echo "=== 13. API TFO (debe incluir T1, T2, T3) ==="
curl -s "http://localhost:8000/audit/tfo/${USER_ID}" || echo "(fallo)"
echo ""
echo ""

echo "=== 14. Logs Core User Service ==="
docker logs poc5_gdpr_core_user_service 2>&1 | tail -50
echo ""

echo "=== 15. Logs Core Reader ==="
docker logs poc5_gdpr_core_reader 2>&1 | tail -40
echo ""

echo "=== 16. Logs Core Reservations ==="
docker logs poc5_gdpr_core_reservations 2>&1 | tail -40
echo ""

echo "=== 17. Logs Apoyo Analytics ==="
docker logs poc5_gdpr_apoyo_analytics 2>&1 | tail -40
echo ""

echo "=== FIN. Abre $OUT y copia cada sección al informe (Anexo A y B). ==="
