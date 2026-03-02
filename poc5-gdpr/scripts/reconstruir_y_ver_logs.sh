#!/usr/bin/env bash
# Reconstruye los consumidores, reinicia el entorno y muestra los logs.
# Uso: desde poc5-gdpr → ./scripts/reconstruir_y_ver_logs.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
USER_ID="${USER_ID:-a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11}"

echo "=== Bajando contenedores ==="
docker compose down

echo "=== Reconstruyendo consumidores (sin caché) ==="
docker compose build --no-cache core-reader-service core-reservations-consumer apoyo-analytics-consumer

echo "=== Levantando todo ==="
docker compose up -d

echo "=== Esperando 15 s a que arranquen RabbitMQ y consumidores ==="
sleep 15

echo "=== Estado de contenedores ==="
docker compose ps

echo "=== Disparando derecho al olvido ==="
curl -s -X POST "http://localhost:8000/users/${USER_ID}/derecho-olvido" || true
sleep 3

echo ""
echo "=== Logs Core Reader (últimas 30 líneas) ==="
docker logs poc5_gdpr_core_reader 2>&1 | tail -30

echo ""
echo "=== Logs Core Reservations (últimas 30 líneas) ==="
docker logs poc5_gdpr_core_reservations 2>&1 | tail -30

echo ""
echo "=== Logs Apoyo Analytics (últimas 30 líneas) ==="
docker logs poc5_gdpr_apoyo_analytics 2>&1 | tail -30

echo ""
echo "=== Listo. Para datos frescos la próxima vez: docker compose down -v antes de up -d ==="
