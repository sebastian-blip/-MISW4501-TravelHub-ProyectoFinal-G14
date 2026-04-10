"""
Router para Reservation Service con CQRS.
Endpoints para crear y listar reservaciones.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from mediatr import Mediator

from user_service.utils.security import get_current_user

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


# Modelos Pydantic para requests
class CreateReservationRequest(BaseModel):
    user_id: str
    hotel_id: str
    room_type_id: str
    check_in: date
    check_out: date
    guests: int = 1
    base_price: str = "0.00"
    taxes: str = "0.00"
    discounts: str = "0.00"
    total_price: str = "0.00"
    currency_code: str = "USD"
    cart_id: Optional[str] = None
    cancellation_policy: Optional[str] = None
    special_requests: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    status: str


@router.post("", response_model=CreateReservationResponse)
async def create_reservation(
    request: CreateReservationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Crea una nueva reservación. Requiere autenticación JWT.
    """
    try:
        mediator = Mediator()
        command = CreateReservationCommand(
            user_id=UUID(request.user_id),
            hotel_id=UUID(request.hotel_id),
            room_type_id=UUID(request.room_type_id),
            check_in=request.check_in,
            check_out=request.check_out,
            guests=request.guests,
            base_price=Decimal(request.base_price),
            taxes=Decimal(request.taxes),
            discounts=Decimal(request.discounts),
            total_price=Decimal(request.total_price),
            currency_code=request.currency_code,
            cart_id=UUID(request.cart_id) if request.cart_id else None,
            cancellation_policy=request.cancellation_policy,
            special_requests=request.special_requests,
        )
        result = await mediator.send_async(command)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear reservación: {str(e)}")


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation_by_id(
    reservation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Obtiene una reservación por su ID. Requiere autenticación JWT.
    """
    try:
        mediator = Mediator()
        query = GetReservationByIdQuery(reservation_id=UUID(reservation_id))
        result = await mediator.send_async(query)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener reservación: {str(e)}")


@router.get("/code/{confirmation_code}", response_model=ReservationResponse)
async def get_reservation_by_code(
    confirmation_code: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Obtiene una reservación por su código de confirmación. Requiere autenticación JWT.
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
    user_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Lista todas las reservaciones de un usuario. Requiere autenticación JWT.
    """
    try:
        mediator = Mediator()
        query = ListReservationsByUserQuery(user_id=UUID(user_id), limit=limit, offset=offset)
        result = await mediator.send_async(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar reservaciones: {str(e)}")


@router.get("", response_model=ReservationListResponse)
async def list_all_reservations(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Lista todas las reservaciones (con paginación). Requiere autenticación JWT.
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
    reservation_id: str,
    request: UpdateStatusRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Actualiza el estado de una reservación. Requiere autenticación JWT.
    """
    try:
        mediator = Mediator()
        command = UpdateReservationStatusCommand(
            reservation_id=UUID(reservation_id),
            status=request.status.lower(),
        )
        result = await mediator.send_async(command)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar estado: {str(e)}")
