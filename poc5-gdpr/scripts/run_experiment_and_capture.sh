#!/usr/bin/env bash
# Ejecuta el experimento completo y escribe toda la salida en EXPERIMENTO_SALIDA.txt
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="${OUT:-$ROOT/EXPERIMENTO_SALIDA.txt}"
USER_ID="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

exec > "$OUT" 2>&1
echo "=== $(date -Iseconds) ==="
echo ""
echo "=== docker compose down ==="
docker compose down || true
echo ""
echo "=== docker compose up -d ==="
docker compose up -d
echo ""
echo "=== Esperando 25 s ==="
sleep 25
echo ""
echo "=== docker compose ps ==="
docker compose ps
echo ""
echo "=== Health ==="
curl -s http://localhost:8000/health || echo "(fallo)"
echo ""
echo ""
echo "=== POST derecho-olvido ==="
curl -s -X POST "http://localhost:8000/users/${USER_ID}/derecho-olvido" || echo "(fallo)"
sleep 5
echo ""
echo ""
echo "=== Users ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, email, name, anonymized FROM users WHERE id = '${USER_ID}';" 2>/dev/null || echo "(fallo)"
echo ""
echo "=== User read model ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, email, name, anonymized FROM user_read_model WHERE id = '${USER_ID}';" 2>/dev/null || echo "(fallo)"
echo ""
echo "=== Reservations ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, user_id FROM reservations LIMIT 5;" 2>/dev/null || echo "(fallo)"
echo ""
echo "=== Analytics ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT id, user_id, anonymized FROM analytics_user_activity LIMIT 5;" 2>/dev/null || echo "(fallo)"
echo ""
echo "=== Audit events ==="
docker exec poc5_gdpr_db psql -U postgres -d poc5_gdpr -c "SELECT event_type, user_id, consumer_id, timestamp FROM audit_events ORDER BY timestamp;" 2>/dev/null || echo "(fallo)"
echo ""
echo "=== API TFO ==="
curl -s "http://localhost:8000/audit/tfo/${USER_ID}" || echo "(fallo)"
echo ""
echo ""
echo "=== Logs Core User Service ==="
docker logs poc5_gdpr_core_user_service 2>&1 | tail -40
echo ""
echo "=== Logs Core Reader ==="
docker logs poc5_gdpr_core_reader 2>&1 | tail -30
echo ""
echo "=== Logs Core Reservations ==="
docker logs poc5_gdpr_core_reservations 2>&1 | tail -30
echo ""
echo "=== Logs Apoyo Analytics ==="
docker logs poc5_gdpr_apoyo_analytics 2>&1 | tail -30
echo ""
echo "=== FIN ==="
