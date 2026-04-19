#!/usr/bin/env bash
# Multiple POST /reservation-flow/create attempts + printed I/O reference.
#
# Usage:
#   ./scripts/reservation-flow-multi-try.sh
#   MULTI_TRY_COUNT=12 CORE_URL=http://localhost:8000 ./scripts/reservation-flow-multi-try.sh
#
# Random validate mode (optional): TH_RESERVATION_VALIDATE_MODE=random + TH_MOCK_RESERVATION_EXISTS_RATE
#
# With default PMS mode: Kafka exists=true (no PMS availability) blocks create (pms_blocked).
# DB overlap still blocks when exists=false but a row overlaps. Repeating the SAME dates after
# a success fails validate with overlap.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORE_URL="${CORE_URL:-http://localhost:8000}"
N="${MULTI_TRY_COUNT:-8}"

workflow_doc() {
  cat <<'WORKFLOW'
================================================================================
RESERVATION CREATE FLOW — what goes in / out (service-core)
================================================================================

1) HTTP  POST  /reservation-flow/create
   Content-Type: application/json

   IN (CreateRequest body — main fields):
     user_id            optional UUID string
     hotel_id           required UUID string
     room_type_id       required UUID string
     check_in, check_out required ISO dates (YYYY-MM-DD)
     guests, base_price, taxes, discounts, total_price, currency_code
     primary_guest      { first_name, last_name, document_*, nationality }
     payment            { amount, currency_code, payment_token, provider_id? }
     cart_id, cancellation_policy, special_requests  optional

   OUT — success path (completed: true):
     completed          true
     step               "create"
     history            ["validate", "create"]
     validate           { from_kafka: bool, message: string }
                        from_kafka=true if reservation-validate-results arrived in time
     result             step_create payload (confirmation_code, reservation_id, status,
                        hotel{}, room_type{}, pricing{}, check_in, check_out, message)

   OUT — stopped at validate (completed: false, step: validate):
     result.success      false → missing required fields
     result.proceed      false → Kafka/PMS exists=true (pms_blocked) OR DB overlap (overlap:true)
     result              may include pms_blocked, overlap, confirmation_code of existing row, reservation{}, message

   OUT — stopped at create (completed: false, step: create):
     result              step_create error (success: false, error, message)

2) Kafka (core → external → core) — validate step only

   Topic OUT (producer):  reservation-validate-requests
   Message IN (JSON bytes):
     event              "reservation_validate_request"
     user_id            string (may be empty if guest)
     hotel_id, room_type_id, check_in, check_out  strings
     correlation_id     UUID string

   Topic IN (consumer):   reservation-validate-results
   Message OUT (JSON) — PMS availability (or random mode): exists true/false + message.

   Core: if exists=true → proceed false (pms_blocked), no create. If exists=false → DB overlap query;
   overlap sets proceed false. Kafka failure/timeout → exists treated false in core, continues to DB.

3) Guaranteed failure demo
   Second POST with identical hotel_id, room_type_id, check_in, check_out after a successful
   create for those dates → validate returns overlap → completed:false.

================================================================================
WORKFLOW
}

workflow_doc
echo ""
echo "=== Running $N distinct-date attempts + 1 overlap retry (same body as last success dates) ==="
echo "Core: $CORE_URL"
echo ""

if ! curl -sf "$CORE_URL/health" >/dev/null 2>&1; then
  echo "WARN: $CORE_URL/health not OK — requests may fail."
fi

USER_ID="d1000000-0000-0000-0000-000000000001"
HOTEL_ID="b1000000-0000-0000-0000-000000000001"
ROOM_TYPE_ID="c1000000-0000-0000-0000-000000000101"

last_check_in=""
last_check_out=""
last_success_json=""

for i in $(seq 1 "$N"); do
  check_in="$(python3 -c "from datetime import date, timedelta; print((date(2032, 3, 1) + timedelta(days=$i)).isoformat())")"
  check_out="$(python3 -c "from datetime import date, timedelta; print((date(2032, 3, 1) + timedelta(days=$i + 4)).isoformat())")"

  body="$(python3 -c "
import json
print(json.dumps({
  'user_id': '$USER_ID',
  'hotel_id': '$HOTEL_ID',
  'room_type_id': '$ROOM_TYPE_ID',
  'check_in': '$check_in',
  'check_out': '$check_out',
  'primary_guest': {'first_name': 'Multi', 'last_name': 'Try'},
  'payment': {'amount': '400.00', 'currency_code': 'USD', 'payment_token': 'tok_visa'},
}))
")"

  echo "------------------------------------------------------------------"
  echo "TRY #$i  check_in=$check_in  check_out=$check_out"
  echo "HTTP IN (body):"
  echo "$body" | python3 -m json.tool
  echo "HTTP OUT (raw):"
  resp="$(curl -sS -X POST "$CORE_URL/reservation-flow/create" \
    -H "Content-Type: application/json" \
    -d "$body")"
  echo "$resp" | python3 -m json.tool || echo "$resp"

  completed="$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('completed'))" 2>/dev/null || echo "?")"
  step="$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('step',''))" 2>/dev/null || echo "?")"
  fk="$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); v=d.get('validate') or {}; print(v.get('from_kafka'))" 2>/dev/null || echo "?")"
  code="$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('result') or {}; print(r.get('confirmation_code') or r.get('message','')[:60])" 2>/dev/null || echo "?")"
  echo "SUMMARY: completed=$completed step=$step validate.from_kafka=$fk result_hint=$code"

  if [[ "$completed" == "True" ]]; then
    last_check_in="$check_in"
    last_check_out="$check_out"
    last_success_json="$body"
  fi
done

if [[ -n "$last_success_json" ]]; then
  echo "------------------------------------------------------------------"
  echo "OVERLAP TRY — same payload as last successful create (expect completed false, overlap):"
  echo "HTTP IN:"
  echo "$last_success_json" | python3 -m json.tool
  resp="$(curl -sS -X POST "$CORE_URL/reservation-flow/create" \
    -H "Content-Type: application/json" \
    -d "$last_success_json")"
  echo "HTTP OUT:"
  echo "$resp" | python3 -m json.tool || echo "$resp"
else
  echo "No successful create in this run — skipping overlap retry."
fi

echo ""
echo "Done."
