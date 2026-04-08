"""
Flujo simple de reservación: validate → create → cancelation
Sin dinamismo, pasos fijos y explícitos.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import date

from mediatr import Mediator
from reservation_service.commands import CreateReservationCommand, UpdateReservationStatusCommand
from reservation_service.queries import GetReservationByCodeQuery


class SimpleReservationFlow:
    """
    Flujo de reservación con pasos fijos.
    No usa reflection, todo es explícito.
    """
    
    def __init__(self):
        self.mediator = Mediator()
        self.context: Dict[str, Any] = {}
        self.current_step = "validate"
        self.history = ["validate"]
    
    def set_data(self, **kwargs):
        """Guarda datos para el flujo."""
        self.context.update(kwargs)
    
    # ========== PASO 1: VALIDATE ==========
    async def step_validate(self) -> Dict[str, Any]:
        """
        Paso 1: Busca si ya existe una reserva.
        Retorna: {"proceed": True/False, "exists": True/False, ...}
        """
        from sqlalchemy import select, and_
        from infrastructure.database import async_session_maker
        from domain.models.reservation import Reservation
        
        user_id = self.context.get("user_id")
        hotel_id = self.context.get("hotel_id")
        room_type_id = self.context.get("room_type_id")
        check_in = self.context.get("check_in")
        check_out = self.context.get("check_out")
        
        if not all([user_id, hotel_id, room_type_id, check_in, check_out]):
            return {
                "success": False,
                "proceed": False,
                "error": "Faltan datos obligatorios",
                "missing": [k for k in ["user_id", "hotel_id", "room_type_id", "check_in", "check_out"] 
                           if not self.context.get(k)]
            }
        
        print(f"[Flow] Paso 1 - Validando: user={user_id}, hotel={hotel_id}")
        
        async with async_session_maker() as session:
            stmt = select(Reservation).where(
                and_(
                    Reservation.user_id == UUID(user_id),
                    Reservation.hotel_id == UUID(hotel_id),
                    Reservation.room_type_id == UUID(room_type_id),
                    Reservation.check_in == check_in,
                    Reservation.check_out == check_out,
                    Reservation.status.in_(["pending", "confirmed"])
                )
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                return {
                    "success": True,
                    "proceed": False,  # No continuar, ya existe
                    "exists": True,
                    "confirmation_code": existing.confirmation_code,
                    "message": f"Ya existe reserva: {existing.confirmation_code}",
                    "reservation": {
                        "id": str(existing.id),
                        "status": existing.status,
                        "total_price": str(existing.total_price)
                    }
                }
        
        # No existe, podemos continuar
        return {
            "success": True,
            "proceed": True,  # Continuar al siguiente paso
            "exists": False,
            "message": "No existe reserva. OK para crear."
        }
    
    # ========== PASO 2: CREATE ==========
    async def step_create(self) -> Dict[str, Any]:
        """
        Paso 2: Crea la reservación.
        Solo se ejecuta si step_validate retornó proceed=True.
        """
        print(f"[Flow] Paso 2 - Creando reserva")
        
        # Calcular precio total
        base = Decimal(self.context.get("base_price", "500.00"))
        taxes = Decimal(self.context.get("taxes", "50.00"))
        discounts = Decimal(self.context.get("discounts", "0.00"))
        total = self.context.get("total_price")
        
        if total:
            total_price = Decimal(total)
        else:
            total_price = base + taxes - discounts
        
        try:
            command = CreateReservationCommand(
                user_id=UUID(self.context["user_id"]),
                hotel_id=UUID(self.context["hotel_id"]),
                room_type_id=UUID(self.context["room_type_id"]),
                check_in=self.context["check_in"],
                check_out=self.context["check_out"],
                guests=self.context.get("guests", 1),
                base_price=base,
                taxes=taxes,
                discounts=discounts,
                total_price=total_price,
                special_requests=self.context.get("special_requests"),
            )
            
            result = await self.mediator.send_async(command)
            
            # Guardar para posible cancelación
            self.context["confirmation_code"] = result.confirmation_code
            self.context["reservation_id"] = str(result.id)
            
            return {
                "success": True,
                "proceed": True,
                "confirmation_code": result.confirmation_code,
                "reservation_id": str(result.id),
                "total_price": str(result.total_price),
                "message": f"Reserva creada: {result.confirmation_code}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "proceed": False,
                "error": str(e),
                "message": f"Error al crear: {str(e)}"
            }
    
    # ========== PASO 3: CANCELATION ==========
    async def step_cancelation(self) -> Dict[str, Any]:
        """
        Paso 3: Cancela una reserva existente.
        """
        confirmation_code = self.context.get("confirmation_code")
        
        if not confirmation_code:
            return {
                "success": False,
                "proceed": False,
                "error": "No hay confirmation_code en contexto",
                "message": "Se requiere código de confirmación"
            }
        
        print(f"[Flow] Paso 3 - Cancelando: {confirmation_code}")
        
        try:
            # Buscar la reserva
            query = GetReservationByCodeQuery(confirmation_code=confirmation_code)
            reservation = await self.mediator.send_async(query)
            
            # Cancelar
            command = UpdateReservationStatusCommand(
                reservation_id=UUID(str(reservation.id)),
                status="cancelled"
            )
            result = await self.mediator.send_async(command)
            
            return {
                "success": True,
                "proceed": True,
                "confirmation_code": confirmation_code,
                "previous_status": result.previous_status,
                "new_status": result.new_status,
                "message": f"Reserva {confirmation_code} cancelada"
            }
            
        except Exception as e:
            return {
                "success": False,
                "proceed": False,
                "error": str(e),
                "message": f"Error al cancelar: {str(e)}"
            }
    
    # ========== EJECUCIÓN DEL FLUJO COMPLETO ==========
    async def run_create_flow(self) -> Dict[str, Any]:
        """
        Ejecuta el flujo completo: validate → create
        Si validate falla o encuentra duplicado, se detiene.
        """
        # Paso 1: Validar
        step1 = await self.step_validate()
        self.current_step = "validate"
        
        if not step1["success"]:
            return {"completed": False, "step": "validate", "result": step1}
        
        if not step1["proceed"]:
            # Ya existe, no crear duplicado
            return {"completed": False, "step": "validate", "result": step1}
        
        # Paso 2: Crear
        self.current_step = "create"
        self.history.append("create")
        step2 = await self.step_create()
        
        if not step2["success"]:
            return {"completed": False, "step": "create", "result": step2}
        
        return {
            "completed": True,
            "step": "create",
            "history": self.history,
            "result": step2
        }
    
    async def run_cancel_flow(self, confirmation_code: str) -> Dict[str, Any]:
        """
        Ejecuta el flujo de cancelación.
        """
        self.context["confirmation_code"] = confirmation_code
        self.current_step = "cancelation"
        self.history = ["cancelation"]
        
        result = await self.step_cancelation()
        
        return {
            "completed": result["success"],
            "step": "cancelation",
            "result": result
        }
