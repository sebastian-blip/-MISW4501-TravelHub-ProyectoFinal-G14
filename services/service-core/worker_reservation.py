"""
Worker de reservas: cancela reservas en estado "pending" que superan
el tiempo de expiración configurado y libera el inventario asociado.

Uso:
    python worker_reservation.py

Variables de entorno:
    WORKER_INTERVAL_SECONDS  — segundos entre ciclos (default: 60)
    WORKER_EXPIRATION_MINUTES — minutos para considerar expirada una reserva (default: 5)
"""
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import os
import signal
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Importar para registrar handlers de Mediator
import reservation_service.commands  # noqa: F401
from domain.models.reservation import Reservation
from infrastructure.database import async_session_maker, init_db
from mediatr import Mediator
from reservation_service.commands import UpdateReservationStatusCommand

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("worker_reservation")

INTERVAL_SECONDS = int(os.getenv("WORKER_INTERVAL_SECONDS", "60"))
EXPIRATION_MINUTES = int(os.getenv("WORKER_EXPIRATION_MINUTES", "5"))


async def find_expired_reservation_ids(session: AsyncSession) -> list[str]:
    """Devuelve los IDs de reservas pending creadas hace más de N minutos."""
    cutoff = datetime.utcnow() - timedelta(minutes=EXPIRATION_MINUTES)
    result = await session.execute(
        select(Reservation)
        .where(Reservation.status == "pending")
        .where(Reservation.created_at < cutoff)
        .order_by(Reservation.created_at)
    )
    rows = result.scalars().all()
    return [str(r.id) for r in rows]


async def cancel_reservation(reservation_id: str) -> bool:
    """Envía el command para cancelar la reserva y liberar inventario."""
    try:
        mediator = Mediator()
        command = UpdateReservationStatusCommand(
            reservation_id=reservation_id,
            status="cancelled"
        )
        response = await mediator.send_async(command)
        logger.info(
            f"Reserva {reservation_id} cancelada | "
            f"{response.previous_status} → {response.new_status}"
        )
        return True
    except Exception:
        logger.exception(f"Error cancelando reserva {reservation_id}")
        return False


async def run_once() -> int:
    """Ejecuta un ciclo completo: buscar expiradas y cancelarlas."""
    async with async_session_maker() as session:
        expired_ids = await find_expired_reservation_ids(session)

    if not expired_ids:
        return 0

    logger.info(
        f"Encontradas {len(expired_ids)} reservas expiradas (> {EXPIRATION_MINUTES}min)"
    )

    cancelled = 0
    for rid in expired_ids:
        if await cancel_reservation(rid):
            cancelled += 1

    logger.info(f"Reservas canceladas en este ciclo: {cancelled}/{len(expired_ids)}")
    return cancelled


async def main() -> None:
    logger.info("Worker de reservas iniciando...")
    logger.info(f"Intervalo: {INTERVAL_SECONDS}s | Expiración: {EXPIRATION_MINUTES}min")

    # Asegura que las tablas existen (idempotente). En producción/K8s ya existen,
    # así que si falla solo logueamos warning y seguimos.
    try:
        await init_db()
        logger.info("Base de datos inicializada correctamente")
    except Exception:
        logger.warning("No se pudo inicializar la base de datos (tablas ya existen o credenciales pendientes). Continuando...")

    shutdown_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_event.set)

    while not shutdown_event.is_set():
        try:
            await run_once()
        except Exception:
            logger.exception("Error en ciclo de procesamiento")

        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=INTERVAL_SECONDS)
        except asyncio.TimeoutError:
            pass

    logger.info("Worker detenido gracefully")


if __name__ == "__main__":
    asyncio.run(main())
