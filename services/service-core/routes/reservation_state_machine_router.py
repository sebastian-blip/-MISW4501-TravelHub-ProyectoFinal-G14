"""
Router simple usando flujo explícito de pasos.
Sin dinamismo, todo es directo y fácil de seguir.
"""
from typing import Optional
from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field

from state_machine.simple_reservation_flow import SimpleReservationFlow
from user_service.utils.security import get_current_user_optional

router = APIRouter(prefix="/reservation-flow", tags=["Reservation Flow"])


class PrimaryGuestPaymentRequest(BaseModel):
    first_name: str
    last_name: str
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    nationality: Optional[str] = None
    email: str


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
async def create_reservation(
    request: CreateRequest,
    x_guest_id: Optional[str] = Header(None, alias="X-Guest-Id"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Flujo: validate → create.

    1. Valida si existe reserva duplicada (solapamiento de fechas)
    2. Si no existe, la crea con guest principal y pago
    3. Retorna confirmation_code o error

    Autenticación opcional:
    - Si viene JWT válido, extrae user_id del token (prioridad).
    - Si no viene JWT, usa X-Guest-Id.
    - Si no viene ninguno, retorna 401.
    """
    jwt_user_id = current_user.get("user_id") if current_user else None

    if jwt_user_id:
        user_id = jwt_user_id
        user_guest_id = None
    elif x_guest_id:
        user_id = None
        try:
            user_guest_id = str(UUID(x_guest_id))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="X-Guest-Id debe ser un UUID válido"
            )
    else:
        raise HTTPException(
            status_code=401,
            detail="Se requiere autenticación (Bearer token) o X-Guest-Id"
        )

    try:
        flow = SimpleReservationFlow()
        flow.set_data(
            user_id=user_id,
            user_guest_id=user_guest_id,
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


@router.get("/data/{reservation_id}")
async def data_reservation(reservation_id:str):
    flow = SimpleReservationFlow()
    flow.set_data(reservation_id=reservation_id)
    await flow.data_flow()
    return "coco"


@router.post("/payment")
async def payment_reservation(
    request: ConfirmReservationRequest,
    x_guest_id: Optional[str] = Header(None, alias="X-Guest-Id"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Flujo de pago: validate_time → confirm_payment.

    Autenticación opcional:
    - Si viene JWT válido, extrae user_id del token (prioridad).
    - Si no viene JWT, usa X-Guest-Id.
    - Si no viene ninguno, retorna 401.
    """
    jwt_user_id = current_user.get("user_id") if current_user else None

    if jwt_user_id:
        user_id = jwt_user_id
        user_guest_id = None
    elif x_guest_id:
        user_id = None
        try:
            user_guest_id = str(UUID(x_guest_id))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="X-Guest-Id debe ser un UUID válido"
            )
    else:
        raise HTTPException(
            status_code=401,
            detail="Se requiere autenticación (Bearer token) o X-Guest-Id"
        )

    flow = SimpleReservationFlow()
    flow.set_data(
        reservation_id=request.reservation_id,
        primary_guest=request.primary_guest.model_dump(),
        payment=request.payment.model_dump(),
        user_id=user_id,
        user_guest_id=user_guest_id,
    )
    result = await flow.run_payment_flow()
    return result

