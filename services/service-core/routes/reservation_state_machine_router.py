"""
Router simple usando flujo explícito de pasos.
Sin dinamismo, todo es directo y fácil de seguir.
"""
from typing import Optional
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from state_machine.simple_reservation_flow import SimpleReservationFlow

router = APIRouter(prefix="/reservation-flow", tags=["Reservation Flow"])


class CreateRequest(BaseModel):
    user_id: str
    hotel_id: str
    room_type_id: str
    check_in: date
    check_out: date
    guests: int = 1
    base_price: Optional[str] = "500.00"
    taxes: Optional[str] = "50.00"
    discounts: Optional[str] = "0.00"
    total_price: Optional[str] = None
    special_requests: Optional[str] = None


class CancelRequest(BaseModel):
    confirmation_code: str


@router.post("/create")
async def create_reservation(request: CreateRequest):
    """
    Flujo: validate → create
    
    1. Valida si existe reserva duplicada
    2. Si no existe, la crea
    3. Retorna confirmation_code o error
    """
    try:
        flow = SimpleReservationFlow()
        flow.set_data(
            user_id=request.user_id,
            hotel_id=request.hotel_id,
            room_type_id=request.room_type_id,
            check_in=request.check_in,
            check_out=request.check_out,
            guests=request.guests,
            base_price=request.base_price,
            taxes=request.taxes,
            discounts=request.discounts,
            total_price=request.total_price,
            special_requests=request.special_requests,
        )
        
        result = await flow.run_create_flow()
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel")
async def cancel_reservation(request: CancelRequest):
    """
    Cancela una reserva por código.
    """
    try:
        flow = SimpleReservationFlow()
        result = await flow.run_cancel_flow(request.confirmation_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check/{confirmation_code}")
async def check_reservation(confirmation_code: str):
    """Consulta una reserva por código."""
    from reservation_service.queries import GetReservationByCodeQuery
    from mediatr import Mediator
    
    try:
        mediator = Mediator()
        query = GetReservationByCodeQuery(confirmation_code=confirmation_code)
        reservation = await mediator.send_async(query)
        
        return {
            "exists": True,
            "reservation": {
                "id": str(reservation.id),
                "confirmation_code": reservation.confirmation_code,
                "status": reservation.status,
                "total_price": str(reservation.total_price),
            }
        }
    except ValueError:
        return {"exists": False, "message": "Reserva no encontrada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
