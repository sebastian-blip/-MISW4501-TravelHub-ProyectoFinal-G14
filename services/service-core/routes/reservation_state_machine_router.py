"""
Router simple usando flujo explícito de pasos.
Sin dinamismo, todo es directo y fácil de seguir.
"""
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Header, status
from fastapi.responses import JSONResponse
from state_machine.simple_reservation_flow import SimpleReservationFlow

router = APIRouter(prefix="/reservation-flow", tags=["Reservation Flow"])


class PrimaryGuestPaymentRequest(BaseModel):
    first_name: str
    last_name: str
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    nationality: Optional[str] = None
    email: Optional[str] = None


class PaymentDetailRequest(BaseModel):
    amount: str
    currency_code: str = "USD"
    payment_token: str


class ConfirmReservationRequest(BaseModel):
    reservation_id: str
    primary_guest: PrimaryGuestPaymentRequest
    payment: PaymentDetailRequest



class CreateRequest(BaseModel):
    user_id: Optional[str] = Field(default=None)
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


class CancelRequest(BaseModel):
    confirmation_code: str



@router.post("/create")
async def create_reservation(request: CreateRequest, x_guest_id: str = Header(..., alias="X-Guest-Id")):
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
            currency_code=request.currency_code,
            cart_id=request.cart_id,
            cancellation_policy=request.cancellation_policy,
            special_requests=request.special_requests,
            user_guest_id=x_guest_id,
        )

        result = await flow.run_create_flow()

        if not result["completed"]:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=result
            )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=result
        )

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


@router.get("/data/{reservation_id}")
async def data_reservation(reservation_id:str):
    flow = SimpleReservationFlow()
    flow.set_data(reservation_id=reservation_id)
    await flow.data_flow()
    return "coco"


@router.post("/payment")
async def payment_reservation(request: ConfirmReservationRequest):
    flow = SimpleReservationFlow()
    flow.set_data(
        reservation_id=request.reservation_id,
        primary_guest=request.primary_guest.dict(),
        payment=request.payment.dict(),
    )
    result = await flow.run_payment_flow()
    return result

