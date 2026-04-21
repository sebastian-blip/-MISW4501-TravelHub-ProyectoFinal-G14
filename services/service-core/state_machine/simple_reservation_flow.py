"""
Flujo simple de reservación: validate → create → cancelation
Sin dinamismo, pasos fijos y explícitos.
"""
import uuid
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime

from mediatr import Mediator
from reservation_service.commands import CreateReservationCommand, UpdateReservationStatusCommand
from reservation_service.queries import GetReservationByCodeQuery , GetReservationByIdHandler , GetReservationByIdQuery
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
        self.event = EventMachine(wait_for_reply, async_session_maker)
    
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
        result = await self.event.validate_reservation(publish_reservation_validate,correlation_id, user_id, hotel_id, room_type_id, check_in, check_out
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

    async def data_flow(self):

       try :
            query = GetReservationByIdQuery(reservation_id=UUID(self.context["reservation_id"]))
            reservation = await self.mediator.send_async(query)

            print(reservation)

            return {
                "completed": True,
                "step": "cancelation",
            }

       except Exception as e:


            return {
                "completed": False,
            }

    async def step_validate_time(self) -> Dict[str, Any]:
        from datetime import timezone, timedelta
        from sqlalchemy import select, and_
        from domain.models.reservation import Reservation
        from domain.models.inventory_calendar import InventoryCalendar

        reservation_id = self.context.get("reservation_id")

        if not reservation_id:
            return {
                "success": False,
                "proceed": False,
                "error": "No hay reservation_id en contexto"
            }

        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(Reservation).where(Reservation.id == UUID(reservation_id))
                )
                reservation = result.scalars().first()

                if not reservation:
                    return {
                        "success": False,
                        "proceed": False,
                        "error": "Reserva no encontrada"
                    }

                if reservation.status == "confirmed":
                    return {
                        "success": False,
                        "proceed": False,
                        "error": "La reserva ya está confirmada",
                        "confirmation_code": reservation.confirmation_code
                    }

                if reservation.status == "cancelled":
                    return {
                        "success": False,
                        "proceed": False,
                        "error": "No se puede confirmar una reserva cancelada",
                        "confirmation_code": reservation.confirmation_code
                    }

                ahora = datetime.now(timezone.utc)
                created = reservation.created_at.replace(tzinfo=timezone.utc)
                diferencia = (ahora - created).total_seconds() / 60

                if diferencia > 5:
                    # 1. Cancelar reserva
                    reservation.status = "cancelled"

                    # 2. Liberar disponibilidad por fechas
                    fecha = reservation.check_in
                    while fecha < reservation.check_out:
                        inv_result = await session.execute(
                            select(InventoryCalendar).where(
                                and_(
                                    InventoryCalendar.room_type_id == reservation.room_type_id,
                                    InventoryCalendar.date == fecha
                                )
                            )
                        )
                        inventory = inv_result.scalars().first()
                        if inventory:
                            inventory.available_units += 1

                        fecha += timedelta(days=1)

                    await session.commit()

                    return {
                        "success": True,
                        "proceed": False,
                        "expired": True,
                        "message": f"Reserva expirada ({diferencia:.1f} min). Cancelada y disponibilidad liberada."
                    }

                return {
                    "success": True,
                    "proceed": True,
                    "expired": False,
                    "minutes_remaining": round(5 - diferencia, 1),
                    "message": f"Reserva válida. Quedan {round(5 - diferencia, 1)} minutos."
                }

        except Exception as e:
            return {
                "success": False,
                "proceed": False,
                "error": str(e)
            }

    async def run_payment_flow(self) -> Dict[str, Any]:
        self.current_step = "validate_time"
        self.history = ["validate_time"]

        step1 = await self.step_validate_time()

        if not step1["proceed"]:
            return {"completed": False, "step": "validate_time", "result": step1}

        self.current_step = "confirm_payment"
        self.history.append("confirm_payment")

        step2 = await self.step_confirm_payment()

        if not step2["success"]:
            return {"completed": False, "step": "confirm_payment", "result": step2}

        return {
            "completed": True,
            "step": "confirm_payment",
            "history": self.history,
            "validate_time": {
                "minutes_remaining": step1.get("minutes_remaining"),
                "message": step1.get("message"),
            },
            "result": step2
        }

    async def step_confirm_payment(self) -> Dict[str, Any]:
        from sqlalchemy import select
        from domain.models.reservation import Reservation
        from domain.models.payment import Payment
        from domain.models.reservation_guest import ReservationGuest
        from decimal import Decimal

        reservation_id = self.context.get("reservation_id")
        primary_guest = self.context.get("primary_guest", {})
        payment = self.context.get("payment", {})

        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(Reservation).where(Reservation.id == UUID(reservation_id))
                )
                reservation = result.scalars().first()

                if not reservation:
                    return {
                        "success": False,
                        "proceed": False,
                        "error": "Reserva no encontrada"
                    }

                # 1. Confirmar reserva
                reservation.status = "confirmed"

                # 2. Crear pago
                new_payment = Payment(
                    reservation_id=UUID(reservation_id),
                    provider_id=uuid.UUID('e1000000-0000-0000-0000-000000000002'),  # mock por ahora
                    amount=Decimal(payment.get("amount", "0.00")),
                    currency_code=payment.get("currency_code", "USD"),
                    payment_token=payment.get("payment_token"),
                    status="completed"
                )
                session.add(new_payment)

                # 3. Crear guest principal
                new_guest = ReservationGuest(
                    reservation_id=UUID(reservation_id),
                    first_name=primary_guest.get("first_name", ""),
                    last_name=primary_guest.get("last_name", ""),
                    document_type=primary_guest.get("document_type"),
                    document_number=primary_guest.get("document_number"),
                    nationality=primary_guest.get("nationality"),
                    is_primary=True
                )
                session.add(new_guest)

                await session.commit()

                return {
                    "success": True,
                    "proceed": True,
                    "confirmation_code": reservation.confirmation_code,
                    "status": reservation.status,
                    "payment_status": new_payment.status,
                    "guest": f"{new_guest.first_name} {new_guest.last_name}",
                    "message": "Reserva confirmada exitosamente"
                }

        except Exception as e:
            return {
                "success": False,
                "proceed": False,
                "error": str(e)
            }













