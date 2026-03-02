#!/usr/bin/env bash
# Ejecuta solo el experimento (health, POST derecho-olvido, captura BD/API/logs).
# Los contenedores deben estar ya levantados (docker compose up -d).
# Uso: cd poc5-gdpr && ./scripts/ejecutar_solo_experimento.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="${OUT:-$ROOT/EXPERIMENTO_SALIDA.txt}"
USER_ID="${USER_ID:-a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11}"

echo "=== Experimento (contenedores ya levantados) ==="
echo "Salida en: $OUT"
echo ""

exec > "$OUT" 2>&1
echo "=== $(date -Iseconds 2>/dev/null || date) ==="
echo ""

echo "=== 1. Estado de contenedores ==="
docker compose ps
echo ""

echo "=== 2. Health ==="
curl -s http://localhost:8000/health || echo "(fallo)"
echo ""
echo ""

echo "=== 3. POST derecho-olvido (T0 se registra aquí) ==="
curl -s -X POST "http://localhost:8000/users/${USER_ID}/derecho-olvido" || echo "(fallo)"
echo ""
echo ""

echo "=== 4. Esperando 10 s a que los tres consumidores procesen ==="
sleep 10
echo ""

echo "=== 5. Users ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, email, name, anonymized FROM users WHERE id = '${USER_ID}';" 2>/dev/null || echo "(fallo)"
echo ""

echo "=== 6. User read model ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, email, name, anonymized FROM user_read_model WHERE id = '${USER_ID}';" 2>/dev/null || echo "(fallo)"
echo ""

echo "=== 7. Reservations ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, user_id FROM reservations LIMIT 5;" 2>/dev/null || echo "(fallo)"
echo ""

echo "=== 8. Analytics ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, user_id, anonymized FROM analytics_user_activity LIMIT 5;" 2>/dev/null || echo "(fallo)"
echo ""

echo "=== 9. Audit events (1 solicitud_olvido + 3 completado) ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT event_type, user_id, consumer_id, timestamp FROM audit_events ORDER BY timestamp;" 2>/dev/null || echo "(fallo)"
echo ""

echo "=== 10. API TFO ==="
curl -s "http://localhost:8000/audit/tfo/${USER_ID}" || echo "(fallo)"
echo ""
echo ""

echo "=== 11. Logs Core User Service ==="
docker logs poc5_gdpr_core_user_service 2>&1 | tail -50
echo ""

echo "=== 12. Logs Core Reader ==="
docker logs poc5_gdpr_core_reader 2>&1 | tail -40
echo ""

echo "=== 13. Logs Core Reservations ==="
docker logs poc5_gdpr_core_reservations 2>&1 | tail -40
echo ""

echo "=== 14. Logs Apoyo Analytics ==="
docker logs poc5_gdpr_apoyo_analytics 2>&1 | tail -40
echo ""

echo "=== FIN. Abre $OUT y copia al informe (Anexo A y B), o avisa para que actualice el informe. ==="
