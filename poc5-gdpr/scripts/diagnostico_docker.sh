#!/usr/bin/env bash
# Diagnóstico: por qué no corre la imagen. Ejecutar desde poc5-gdpr.
# Uso: cd poc5-gdpr && ./scripts/diagnostico_docker.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== 1. Directorio actual (debe ser poc5-gdpr) ==="
pwd
echo ""

echo "=== 2. Docker instalado y daemon activo ==="
docker info 2>&1 | head -5 || { echo "ERROR: Docker no responde. ¿Está Docker Desktop abierto?"; exit 1; }
echo ""

echo "=== 3. Build con salida visible (core-user-service) ==="
docker compose build --progress=plain core-user-service 2>&1
echo ""

echo "=== 4. Levantar solo DB y RabbitMQ primero ==="
docker compose up -d db rabbitmq
echo "Esperando 15 s a que postgres y rabbitmq estén healthy..."
sleep 15
docker compose ps
echo ""

echo "=== 5. Levantar el resto ==="
docker compose up -d
sleep 5
echo ""

echo "=== 6. Estado de contenedores ==="
docker compose ps -a
echo ""

echo "=== 7. Si algún contenedor está Exited, sus logs ==="
for c in poc5_gdpr_core_user_service poc5_gdpr_core_reader poc5_gdpr_core_reservations poc5_gdpr_apoyo_analytics; do
  s=$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null || true)
  if [ "$s" = "exited" ]; then
    echo "--- Logs de $c (exited) ---"
    docker logs "$c" 2>&1 | tail -40
    echo ""
  fi
done
echo ""

echo "=== 8. Health (si core-user-service está up) ==="
curl -s http://localhost:8000/health || echo "(no responde)"
echo ""
echo ""
echo "Fin diagnóstico. Revisa si algún build falló o si los logs muestran un error de Python/conexión."
