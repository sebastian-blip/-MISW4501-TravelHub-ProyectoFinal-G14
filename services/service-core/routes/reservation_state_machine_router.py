"""
Router simplificado que integra máquina de estados con reservaciones.
No expone IDs de tareas (manejo interno).
"""
from typing import Optional, Dict, Any
from datetime import date
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mediatr import Mediator
from state_machine import TaskStateMachine, Meta, ReservationIntegration

router = APIRouter(prefix="/reservation-flow", tags=["Reservation Flow"])


# Modelos Pydantic
class ValidateRequest(BaseModel):
    """Datos para buscar/validar reserva existente"""
    user_id: str
    hotel_id: str
    room_type_id: str
    check_in: date
    check_out: date


class CreateRequest(BaseModel):
    """Datos para crear la reservación"""
    user_id: str
    hotel_id: str
    room_type_id: str
    check_in: date
    check_out: date
    guests: int = 1
    base_price: str = "500.00"
    taxes: str = "50.00"
    discounts: str = "0.00"
    total_price: Optional[str] = None
    currency_code: str = "USD"
    special_requests: Optional[str] = None


class CancelRequest(BaseModel):
    """Datos para cancelar por código"""
    confirmation_code: str
    reason: Optional[str] = None


class FlowResponse(BaseModel):
    """Respuesta estándar del flujo"""
    success: bool
    state: str
    result: Optional[Dict[str, Any]] = None
    message: str


@router.post("/validate", response_model=FlowResponse)
async def validate_reservation(request: ValidateRequest):
    """
    PASO 1 - VALIDATE: Busca si existe una reserva con estas características.
    Si existe, la retorna. Si no, permite crear una nueva.
    """
    try:
        integration = ReservationIntegration()
        
        result = await integration.check_existing_reservation(
            user_id=request.user_id,
            hotel_id=request.hotel_id,
            room_type_id=request.room_type_id,
            check_in=request.check_in,
            check_out=request.check_out,
        )
        
        if result["exists"]:
            return FlowResponse(
                success=True,
                state=Meta.VALIDATE,
                result=result,
                message=f"Reserva existente encontrada: {result['reservation']['confirmation_code']}"
            )
        
        return FlowResponse(
            success=True,
            state=Meta.VALIDATE,
            result=result,
            message="No existe reserva previa. Procede a crear una nueva."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en validación: {str(e)}")


@router.post("/create", response_model=FlowResponse)
async def create_reservation(request: CreateRequest):
    """
    PASO 2 - CREATE: Crea la reservación real.
    Primero valida que no exista duplicado, luego crea.
    """
    try:
        integration = ReservationIntegration()
        mediator = Mediator()
        
        # Primero verificar que no exista (doble check)
        check = await integration.check_existing_reservation(
            user_id=request.user_id,
            hotel_id=request.hotel_id,
            room_type_id=request.room_type_id,
            check_in=request.check_in,
            check_out=request.check_out,
        )
        
        if check["exists"]:
            return FlowResponse(
                success=False,
                state=Meta.VALIDATE,
                result=check,
                message=f"Ya existe una reserva: {check['reservation']['confirmation_code']}. No se puede duplicar."
            )
        
        # Crear la reservación
        from reservation_service.commands import CreateReservationCommand
        from decimal import Decimal
        from uuid import UUID
        
        total = request.total_price
        if total is None:
            calculated = Decimal(request.base_price) + Decimal(request.taxes) - Decimal(request.discounts)
            total = str(calculated)
        
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
            total_price=Decimal(total),
            currency_code=request.currency_code,
            special_requests=request.special_requests,
        )
        
        result = await mediator.send_async(command)
        
        return FlowResponse(
            success=True,
            state=Meta.CREATE,
            result={
                "id": str(result.id),
                "confirmation_code": result.confirmation_code,
                "total_price": str(result.total_price),
                "status": result.status,
            },
            message=f"Reservación creada exitosamente. Código: {result.confirmation_code}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear: {str(e)}")


@router.post("/cancel", response_model=FlowResponse)
async def cancel_reservation(request: CancelRequest):
    """
    PASO 3 - CANCELATION: Cancela una reservación por su código.
    """
    try:
        mediator = Mediator()
        
        from reservation_service.commands import UpdateReservationStatusCommand
        from reservation_service.queries import GetReservationByCodeQuery
        from uuid import UUID
        
        # Buscar la reserva por código
        query = GetReservationByCodeQuery(confirmation_code=request.confirmation_code)
        reservation = await mediator.send_async(query)
        
        # Cancelar
        command = UpdateReservationStatusCommand(
            reservation_id=UUID(str(reservation.id)),
            status="cancelled"
        )
        
        result = await mediator.send_async(command)
        
        return FlowResponse(
            success=True,
            state=Meta.CANCELATION,
            result={
                "confirmation_code": request.confirmation_code,
                "previous_status": result.previous_status,
                "new_status": result.new_status,
            },
            message=f"Reservación {request.confirmation_code} cancelada exitosamente."
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cancelar: {str(e)}")


@router.get("/check/{confirmation_code}", response_model=FlowResponse)
async def check_reservation(confirmation_code: str):
    """
    Consulta una reservación por su código (sin cambiar estado).
    """
    try:
        mediator = Mediator()
        from reservation_service.queries import GetReservationByCodeQuery
        
        query = GetReservationByCodeQuery(confirmation_code=confirmation_code)
        reservation = await mediator.send_async(query)
        
        return FlowResponse(
            success=True,
            state="consulta",
            result={
                "id": str(reservation.id),
                "confirmation_code": reservation.confirmation_code,
                "status": reservation.status,
                "total_price": str(reservation.total_price),
                "check_in": reservation.check_in.isoformat(),
                "check_out": reservation.check_out.isoformat(),
            },
            message=f"Reservación encontrada: {confirmation_code}"
        )
        
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Reservación {confirmation_code} no encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
