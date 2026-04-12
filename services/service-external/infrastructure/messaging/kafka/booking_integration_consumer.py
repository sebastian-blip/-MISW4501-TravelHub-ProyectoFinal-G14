"""
Booking integration consumer — **fully mocked** (no real payment gateway, no real PMS).

Outcomes are randomized:
- ``TH_MOCK_PAYMENT_SUCCESS_RATE`` / ``TH_MOCK_PMS_SUCCESS_RATE`` (independent Bernoulli trials).

When DB writes are enabled, we persist like a real integration would, using the **reservation's**
``total_price`` and ``currency_code`` from PostgreSQL when the row exists (otherwise the Kafka payload).
Payment and inventory updates always use that charge currency; inventory rows are only decremented
when ``inventory_calendar.currency_code`` matches the charge currency (see ``schemas/db.sql``).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from sqlalchemy import and_, select

from domain.models.inventory_calendar import InventoryCalendar
from domain.models.payment import Payment
from domain.models.payment_transaction import PaymentTransaction
from domain.models.pms_sync_log import PmsSyncLog
from domain.models.reservation import Reservation
from infrastructure.database import async_session_maker
from infrastructure.messaging.kafka._kafka_config import consumer_base_config, producer_base_config
from infrastructure.messaging.kafka.topics import (
    TOPIC_BOOKING_INTEGRATION,
    TOPIC_BOOKING_INTEGRATION_RESULTS,
)

_consumer: AIOKafkaConsumer | None = None
_producer: AIOKafkaProducer | None = None
_task: asyncio.Task | None = None

_PAYMENT_OK_RATE = float(os.getenv("TH_MOCK_PAYMENT_SUCCESS_RATE", "0.7"))
_PMS_OK_RATE = float(os.getenv("TH_MOCK_PMS_SUCCESS_RATE", "0.7"))
_DEFAULT_PROVIDER_ID = UUID("e1000000-0000-0000-0000-000000000001")  # seed_reservations.sql Stripe

_ISO4217_RE = re.compile(r"^[A-Z]{3}$")


def _db_enabled() -> bool:
    return os.getenv("TH_BOOKING_DB_UPDATES", "true").lower() in ("1", "true", "yes")


def _dec(v) -> Decimal:
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _normalize_currency(code: str) -> str:
    """ISO 4217-style 3-letter code; invalid or short values fall back to USD."""
    raw = (code or "USD").strip().upper()
    c = raw[:3] if len(raw) >= 3 else "USD"
    if _ISO4217_RE.match(c):
        return c
    logging.warning("[service-external] invalid currency_code %r — using USD", code)
    return "USD"


async def start_booking_integration_consumer(bootstrap_servers: str) -> None:
    global _consumer, _producer, _task
    if _consumer is not None:
        return

    pcfg = producer_base_config(bootstrap_servers)
    _producer = AIOKafkaProducer(**pcfg)
    await _producer.start()

    ccfg = consumer_base_config(bootstrap_servers, "service-external-booking-group")
    _consumer = AIOKafkaConsumer(TOPIC_BOOKING_INTEGRATION, **ccfg)
    await _consumer.start()
    _task = asyncio.create_task(_consume_loop())
    logging.info(
        "[service-external] booking consumer (mock payment+PMS, no external APIs) %s → %s db=%s",
        TOPIC_BOOKING_INTEGRATION,
        TOPIC_BOOKING_INTEGRATION_RESULTS,
        _db_enabled(),
    )


async def stop_booking_integration_consumer() -> None:
    global _consumer, _producer, _task
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
    if _consumer:
        await _consumer.stop()
        _consumer = None
    if _producer:
        await _producer.stop()
        _producer = None


async def _consume_loop() -> None:
    assert _consumer is not None
    try:
        async for msg in _consumer:
            payload = json.loads(msg.value.decode("utf-8"))
            await _handle_booking(payload)
    except asyncio.CancelledError:
        pass


async def _apply_db_writes(
    *,
    payload: dict,
    payment_ok: bool,
    pms_ok: bool,
    payload_total: Decimal,
    payload_currency: str,
    pms_name: str,
    now: datetime,
) -> tuple[bool, str | None, Decimal, str]:
    """Returns (ok, error_message, charge_amount, charge_currency)."""
    hotel_id = UUID(payload["hotel_id"])
    reservation_id = UUID(payload["reservation_id"])
    room_type_id = UUID(payload["room_type_id"])
    check_in = date.fromisoformat(payload["check_in"])
    check_out = date.fromisoformat(payload["check_out"])
    provider_id = UUID(payload["provider_id"]) if payload.get("provider_id") else _DEFAULT_PROVIDER_ID

    charge_amount = payload_total
    charge_currency = _normalize_currency(payload_currency)

    try:
        async with async_session_maker() as session:
            session.add(
                PmsSyncLog(
                    id=uuid4(),
                    hotel_id=hotel_id,
                    pms_provider=pms_name,
                    sync_type="reservations",
                    status="success" if pms_ok else "failed",
                    records_synced=1 if pms_ok else 0,
                    error_message=None if pms_ok else "mock_random_pms_failure",
                    started_at=now,
                    completed_at=now,
                )
            )

            res = await session.get(Reservation, reservation_id)
            if res is None:
                await session.commit()
                logging.warning(
                    "[service-external] booking_integration: no reservation %s; only pms_sync_log written",
                    reservation_id,
                )
                return True, None, charge_amount, charge_currency

            charge_amount = res.total_price
            charge_currency = _normalize_currency(res.currency_code)

            existing_pay = (
                await session.execute(select(Payment).where(Payment.reservation_id == reservation_id))
            ).scalars().first()

            if existing_pay:
                payment = existing_pay
                payment_id = payment.id
            else:
                payment_id = uuid4()
                payment = Payment(
                    id=payment_id,
                    reservation_id=reservation_id,
                    provider_id=provider_id,
                    amount=charge_amount,
                    currency_code=charge_currency,
                    status="pending",
                    payment_token=f"tok_mock_{uuid4().hex[:10]}",
                )
                session.add(payment)

            if payment_ok:
                payment.status = "completed"
                payment.amount = charge_amount
                payment.currency_code = charge_currency
                payment.provider_payment_id = f"pi_mock_{uuid4().hex[:12]}"
                payment.processed_at = now
                payment.updated_at = now
                session.add(
                    PaymentTransaction(
                        id=uuid4(),
                        payment_id=payment_id,
                        type="charge",
                        amount=charge_amount,
                        status="completed",
                        provider_tx_id=f"txn_{uuid4().hex[:10]}",
                    )
                )
            else:
                payment.status = "failed"
                payment.amount = charge_amount
                payment.currency_code = charge_currency
                payment.failure_reason = "mock_random_payment_failure"
                payment.updated_at = now
                session.add(
                    PaymentTransaction(
                        id=uuid4(),
                        payment_id=payment_id,
                        type="charge",
                        amount=charge_amount,
                        status="failed",
                        provider_tx_id=None,
                    )
                )

            if payment_ok:
                res.status = "confirmed"
                res.updated_at = now
                if pms_ok:
                    night = check_in
                    while night < check_out:
                        row = (
                            await session.execute(
                                select(InventoryCalendar).where(
                                    and_(
                                        InventoryCalendar.room_type_id == room_type_id,
                                        InventoryCalendar.date == night,
                                        InventoryCalendar.currency_code == charge_currency,
                                    )
                                )
                            )
                        ).scalars().first()
                        if row is not None and row.available_units > 0:
                            row.available_units = row.available_units - 1
                            row.updated_at = now
                            session.add(row)
                        elif pms_ok and payment_ok:
                            logging.debug(
                                "[service-external] no inventory row for %s %s %s",
                                room_type_id,
                                night,
                                charge_currency,
                            )
                        night += timedelta(days=1)
            else:
                res.status = "cancelled"
                res.updated_at = now

            await session.commit()
        return True, None, charge_amount, charge_currency
    except Exception as e:
        logging.exception("[service-external] booking_integration DB error")
        return False, str(e), charge_amount, charge_currency


async def _handle_booking(payload: dict) -> None:
    assert _producer is not None
    if payload.get("event") != "booking_integration":
        return

    correlation_id = payload.get("correlation_id", "")
    reservation_id = payload.get("reservation_id", "")

    # Independent random outcomes — no calls to external PMS or payment providers.
    payment_ok = random.random() < _PAYMENT_OK_RATE
    pms_ok = random.random() < _PMS_OK_RATE

    now = datetime.now(timezone.utc)
    payload_total = _dec(payload.get("total_price", "0"))
    payload_currency = _normalize_currency(str(payload.get("currency_code", "USD")))
    pms_name = payload.get("pms_provider") or "MockPMS"

    db_ok: bool | None = None
    db_error: str | None = None
    charge_amount = payload_total
    charge_currency = payload_currency
    if _db_enabled():
        db_ok, db_error, charge_amount, charge_currency = await _apply_db_writes(
            payload=payload,
            payment_ok=payment_ok,
            pms_ok=pms_ok,
            payload_total=payload_total,
            payload_currency=payload_currency,
            pms_name=pms_name,
            now=now,
        )
    else:
        db_ok = None

    mock_payment_id = str(uuid4())
    reply = {
        "event": "booking_integration_result",
        "correlation_id": correlation_id,
        "reservation_id": reservation_id,
        "payment_ok": payment_ok,
        "pms_ok": pms_ok,
        "mock_payment_id": mock_payment_id,
        "mock_provider_payment_id": f"pi_mock_{uuid4().hex[:12]}" if payment_ok else None,
        "amount": str(charge_amount),
        "currency_code": charge_currency,
        "reservation_status_mock": "confirmed" if payment_ok else "cancelled",
        "processed_at_iso": now.isoformat(),
        "message": "mock_payment_and_pms_no_external_services",
        "db_writes_enabled": _db_enabled(),
        "db_commit_ok": db_ok,
        "db_error": db_error,
    }

    await _producer.send_and_wait(
        TOPIC_BOOKING_INTEGRATION_RESULTS,
        json.dumps(reply).encode("utf-8"),
    )
    logging.info(
        "[service-external] booking_integration reservation=%s payment_ok=%s pms_ok=%s %s %s db_ok=%s",
        reservation_id,
        payment_ok,
        pms_ok,
        charge_currency,
        charge_amount,
        db_ok,
    )
