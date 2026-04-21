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
from .event_machine import EventMachine
from infrastructure.messaging.kafka.producer import publish_reservation_validate
from infrastructure.messaging.kafka.reply_consumer import wait_for_reply
from infrastructure.database import async_session_maker


class SimpleReservationFlow:


    def __init__(self):
        self.mediator = Mediator()
        self.context: Dict[str, Any] = {}
        self.current_step = "validate"
        self.history = ["validate"]
        self.event = EventMachine(publish_reservation_validate, wait_for_reply, async_session_maker)
    
    def set_data(self, **kwargs):
        """Guarda datos para el flujo."""
        self.context.update(kwargs)
    
    # ========== PASO 1: VALIDATE ==========
    async def step_validate(self) -> Dict[str, Any]:
        import uuid

        user_id = self.context.get("user_id")
        hotel_id = self.context.get("hotel_id")
        room_type_id = self.context.get("room_type_id")
        check_in = self.context.get("check_in")
        check_out = self.context.get("check_out")

        required_fields = ["hotel_id", "room_type_id", "check_in", "check_out"]
        if not all([hotel_id, room_type_id, check_in, check_out]):
            return {
                "success": False,
                "proceed": False,
                "error": "Faltan datos obligatorios",
                "missing": [k for k in required_fields if not self.context.get(k)]
            }

        correlation_id = str(uuid.uuid4())
        result = await self.event.validate_reservation(
            correlation_id, user_id, hotel_id, room_type_id, check_in, check_out
        )

        if result is None:
            return {
                "success": True,
                "proceed": True,
                "exists": False,
                "from_kafka": False,
                "message": "Kafka no disponible, sin validación externa."
            }

        return result
    
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
            # user_id es opcional (puede ser reserva de invitado)
            user_id = UUID(self.context["user_id"]) if self.context.get("user_id") else None
            user_guest_id = UUID(self.context["user_guest_id"]) if self.context.get("user_guest_id") else None
            
            command = CreateReservationCommand(
                user_id=user_id,
                user_guest_id=user_guest_id,
                hotel_id=UUID(self.context["hotel_id"]),
                room_type_id=UUID(self.context["room_type_id"]),
                check_in=self.context["check_in"],
                check_out=self.context["check_out"],
                primary_guest=self.context.get("primary_guest"),
                payment=self.context.get("payment"),
                guests=self.context.get("guests", 1),
                base_price=base,
                taxes=taxes,
                discounts=discounts,
                total_price=total_price,
                currency_code=self.context.get("currency_code", "USD"),
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
                "status": result.status,
                "message": result.message,
                "hotel": {
                    "id": str(result.hotel.id),
                    "name": result.hotel.name,
                    "description": result.hotel.description,
                    "address": result.hotel.address,
                    "city": result.hotel.city,
                    "stars": result.hotel.stars,
                    "rating": str(result.hotel.rating) if result.hotel.rating else None,
                },
                "room_type": {
                    "id": str(result.room_type.id),
                    "name": result.room_type.name,
                    "description": result.room_type.description,
                    "max_capacity": result.room_type.max_capacity,
                    "bed_type": result.room_type.bed_type,
                    "size_sqm": str(result.room_type.size_sqm) if result.room_type.size_sqm else None,
                },
                "pricing": {
                    "nights": result.pricing.nights,
                    "guests": result.pricing.guests,
                    "price_per_night": str(result.pricing.price_per_night),
                    "subtotal": str(result.pricing.subtotal),
                    "taxes": str(result.pricing.taxes),
                    "discounts": str(result.pricing.discounts),
                    "total": str(result.pricing.total),
                    "currency_code": result.pricing.currency_code,
                },
                "check_in": str(result.check_in),
                "check_out": str(result.check_out),
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
            "validate": {
                "from_kafka": step1.get("from_kafka"),
                "message": step1.get("message"),
            },
            "result": step2,
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
