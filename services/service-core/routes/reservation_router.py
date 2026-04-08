"""
Router para Reservation Service con CQRS.
Endpoints para crear y listar reservaciones.
"""
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import date

from fastapi import APIRouter, HTTPException, Query
from mediatr import Mediator

from reservation_service.commands import (
    CreateReservationCommand,
    CreateReservationResponse,
    UpdateReservationStatusCommand,
    UpdateReservationStatusResponse,
)
from reservation_service.queries import (
    GetReservationByIdQuery,
    GetReservationByCodeQuery,
    ListReservationsByUserQuery,
    ListAllReservationsQuery,
    ReservationListResponse,
    ReservationResponse,
)

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post("", response_model=CreateReservationResponse)
async def create_reservation(
    user_id: UUID,
    hotel_id: UUID,
    room_type_id: UUID,
    check_in: date,
    check_out: date,
    guests: int = 1,
    base_price: Decimal = Decimal("0.00"),
    taxes: Decimal = Decimal("0.00"),
    discounts: Decimal = Decimal("0.00"),
    total_price: Decimal = Decimal("0.00"),
    currency_code: str = "USD",
    cart_id: Optional[UUID] = None,
    cancellation_policy: Optional[str] = None,
    special_requests: Optional[str] = None,
):
    """
    Crea una nueva reservación.
    """
    try:
        mediator = Mediator()
        command = CreateReservationCommand(
            user_id=user_id,
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            base_price=base_price,
            taxes=taxes,
            discounts=discounts,
            total_price=total_price,
            currency_code=currency_code,
            cart_id=cart_id,
            cancellation_policy=cancellation_policy,
            special_requests=special_requests,
        )
        result = await mediator.send_async(command)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear reservación: {str(e)}")


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation_by_id(reservation_id: UUID):
    """
    Obtiene una reservación por su ID.
    """
    try:
        mediator = Mediator()
        query = GetReservationByIdQuery(reservation_id=reservation_id)
        result = await mediator.send_async(query)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener reservación: {str(e)}")


@router.get("/code/{confirmation_code}", response_model=ReservationResponse)
async def get_reservation_by_code(confirmation_code: str):
    """
    Obtiene una reservación por su código de confirmación.
    """
    try:
        mediator = Mediator()
        query = GetReservationByCodeQuery(confirmation_code=confirmation_code)
        result = await mediator.send_async(query)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener reservación: {str(e)}")


@router.get("/user/{user_id}", response_model=ReservationListResponse)
async def list_reservations_by_user(
    user_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Lista todas las reservaciones de un usuario.
    """
    try:
        mediator = Mediator()
        query = ListReservationsByUserQuery(user_id=user_id, limit=limit, offset=offset)
        result = await mediator.send_async(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar reservaciones: {str(e)}")


@router.get("", response_model=ReservationListResponse)
async def list_all_reservations(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Lista todas las reservaciones (con paginación).
    """
    try:
        mediator = Mediator()
        query = ListAllReservationsQuery(limit=limit, offset=offset)
        result = await mediator.send_async(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar reservaciones: {str(e)}")


@router.patch("/{reservation_id}/status", response_model=UpdateReservationStatusResponse)
async def update_reservation_status(
    reservation_id: UUID,
    status: str,  # pending, confirmed, cancelled, completed
):
    """
    Actualiza el estado de una reservación.
    """
    try:
        mediator = Mediator()
        command = UpdateReservationStatusCommand(
            reservation_id=reservation_id,
            status=status.lower(),
        )
        result = await mediator.send_async(command)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar estado: {str(e)}")
