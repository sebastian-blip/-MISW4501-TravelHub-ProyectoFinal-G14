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
echo "=== Users (DuckDB API) ==="
curl -s "http://localhost:8080/users/${USER_ID}" 2>/dev/null || echo "(fallo)"
echo ""
echo "=== User read model ==="
curl -s "http://localhost:8080/evidence/read-model" 2>/dev/null || echo "(fallo)"
echo ""
echo "=== Reservations ==="
curl -s "http://localhost:8080/evidence/reservations" 2>/dev/null || echo "(fallo)"
echo ""
echo "=== Analytics ==="
curl -s "http://localhost:8080/evidence/analytics" 2>/dev/null || echo "(fallo)"
echo ""
echo "=== Audit events ==="
curl -s "http://localhost:8080/audit/events" 2>/dev/null || echo "(fallo)"
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
