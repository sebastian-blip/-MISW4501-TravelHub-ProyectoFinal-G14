#!/usr/bin/env bash
# Load SQL seeds against RDS (from .env) and smoke-test POST /reservation-flow/create.
# Prerequisites: .env with POSTGRES_* ; docker compose -f docker-compose.full-stack.yml up -d --build
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env — copy .env.example to .env and set POSTGRES_PASSWORD (and host/db if needed)."
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${POSTGRES_HOST:?POSTGRES_HOST must be set in .env}"
: "${POSTGRES_USER:?POSTGRES_USER must be set in .env}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set in .env}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-postgres}"
POSTGRES_SSL="${POSTGRES_SSL:-require}"

export PGPASSWORD="$POSTGRES_PASSWORD"
if [[ "$POSTGRES_SSL" == "require" ]] || [[ "$POSTGRES_SSL" == "true" ]] || [[ "$POSTGRES_SSL" == "1" ]]; then
  export PGSSLMODE=require
else
  export PGSSLMODE="${PGSSLMODE:-prefer}"
fi

COMPOSE=(docker compose -f docker-compose.full-stack.yml)

echo "Waiting for RDS (pg_isready)..."
for _ in $(seq 1 60); do
  if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
  echo "RDS not reachable from this host (security group / VPN / SSL?). Check PGSSLMODE and network."
  exit 1
fi

HAS_HOTELS="$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT to_regclass('public.hotels');" 2>/dev/null | tr -d '[:space:]' || true)"
if [[ -z "$HAS_HOTELS" ]]; then
  echo "Applying schemas (first run on this database)..."
  psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -f schemas/db.sql
  psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -f schemas/seed_hotels.sql
  psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -f schemas/seed_reservations.sql
  echo "Seeds applied."
else
  echo "Postgres already has public.hotels — skipping DDL/seed scripts."
fi

echo "Waiting for service-core / service-external..."
for _ in $(seq 1 60); do
  if curl -sf "http://localhost:8000/health" >/dev/null && curl -sf "http://localhost:8002/health" >/dev/null; then
    break
  fi
  sleep 2
done

BODY='{
  "user_id": "d1000000-0000-0000-0000-000000000001",
  "hotel_id": "b1000000-0000-0000-0000-000000000001",
  "room_type_id": "c1000000-0000-0000-0000-000000000101",
  "check_in": "2031-06-01",
  "check_out": "2031-06-05",
  "primary_guest": {"first_name": "Smoke", "last_name": "Test"},
  "payment": {"amount": "400.00", "currency_code": "USD", "payment_token": "tok_visa"}
}'

echo ""
echo "=== 1) reservation-flow/create (expect success) ==="
curl -sS -X POST "http://localhost:8000/reservation-flow/create" \
  -H "Content-Type: application/json" \
  -d "$BODY" | python3 -m json.tool || true

echo ""
echo "=== 2) Same request again (expect validate overlap / no second create) ==="
curl -sS -X POST "http://localhost:8000/reservation-flow/create" \
  -H "Content-Type: application/json" \
  -d "$BODY" | python3 -m json.tool || true

echo ""
echo "Done. Core: http://localhost:8000/docs  External: http://localhost:8002/docs"
