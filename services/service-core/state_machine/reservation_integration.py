"""
Integración entre la máquina de estados y el reservation_service.
Cada estado ejecuta acciones reales sobre reservaciones.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import date

from mediatr import Mediator

from reservation_service.commands import (
    CreateReservationCommand,
    CreateReservationResponse,
    UpdateReservationStatusCommand,
)
from reservation_service.queries import (
    GetReservationByIdQuery,
    GetReservationByCodeQuery,
    ReservationResponse,
)


class ReservationIntegration:
    """
    Integración que permite a la máquina de estados ejecutar operaciones
    reales sobre reservaciones en cada paso.
    """
    
    def __init__(self):
        self.mediator = Mediator()
        self._context: Dict[str, Any] = {}  # Para guardar datos entre estados
    
    def set_context(self, key: str, value: Any):
        """Guarda datos en el contexto para uso entre estados."""
        self._context[key] = value
    
    def get_context(self, key: str, default=None) -> Any:
        """Obtiene datos del contexto."""
        return self._context.get(key, default)
    
    # ========== FUNCIONES PARA ESTADO VALIDATE ==========
    
    async def check_existing_reservation(
        self,
        user_id: str,
        hotel_id: str,
        room_type_id: str,
        check_in: date,
        check_out: date,
    ) -> Dict[str, Any]:
        """
        Busca si ya existe una reserva con las mismas características.
        
        Returns:
            Dict con resultado:
            - exists: True/False
            - reservation: datos de la reserva existente (si existe)
            - message: mensaje descriptivo
        """
        from sqlalchemy import select, and_
        from infrastructure.database import async_session_maker
        from domain.models.reservation import Reservation
        
        print(f"[Integration] Buscando reserva existente para user={user_id}, hotel={hotel_id}")
        
        async with async_session_maker() as session:
            # Buscar reservas con las mismas características
            statement = select(Reservation).where(
                and_(
                    Reservation.user_id == UUID(user_id),
                    Reservation.hotel_id == UUID(hotel_id),
                    Reservation.room_type_id == UUID(room_type_id),
                    Reservation.check_in == check_in,
                    Reservation.check_out == check_out,
                    Reservation.status.in_(["pending", "confirmed"])  # No buscar canceladas
                )
            )
            
            result = await session.execute(statement)
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"[Integration] Reserva existente encontrada: {existing.confirmation_code}")
                return {
                    "exists": True,
                    "reservation": {
                        "id": str(existing.id),
                        "confirmation_code": existing.confirmation_code,
                        "status": existing.status,
                        "total_price": str(existing.total_price),
                        "created_at": existing.created_at.isoformat() if existing.created_at else None,
                    },
                    "message": f"Ya existe una reserva con estas características. Código: {existing.confirmation_code}"
                }
        
        # No existe, guardar datos para crear nueva
        print("[Integration] No existe reserva, datos listos para crear nueva")
        
        self.set_context("reservation_data", {
            "user_id": user_id,
            "hotel_id": hotel_id,
            "room_type_id": room_type_id,
            "check_in": check_in,
            "check_out": check_out,
        })
        
        return {
            "exists": False,
            "reservation": None,
            "message": "No existe reserva previa. Puedes crear una nueva."
        }
    
    async def check_user_exists(self, user_id: str) -> bool:
        """Verifica si el usuario existe (simulado)."""
        print(f"[Integration] Verificando usuario {user_id}")
        # Aquí consultarías el user_service real
        return True
    
    async def check_hotel_exists(self, hotel_id: str) -> bool:
        """Verifica si el hotel existe (simulado)."""
        print(f"[Integration] Verificando hotel {hotel_id}")
        return True
    
    # ========== FUNCIONES PARA ESTADO CREATE ==========
    
    async def create_reservation(
        self,
        user_id: Optional[str] = None,
        hotel_id: Optional[str] = None,
        room_type_id: Optional[str] = None,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        guests: int = 1,
        base_price: str = "500.00",
        taxes: str = "50.00",
        discounts: str = "0.00",
        total_price: Optional[str] = None,
        special_requests: Optional[str] = None,
    ) -> CreateReservationResponse:
        """
        Crea la reservación real llamando al reservation_service.
        Puede usar datos del contexto si no se pasan explícitamente.
        """
        # Si no vienen datos, intentar obtener del contexto
        data = self.get_context("reservation_data", {})
        
        user_id = user_id or data.get("user_id")
        hotel_id = hotel_id or data.get("hotel_id")
        room_type_id = room_type_id or data.get("room_type_id")
        check_in = check_in or data.get("check_in")
        check_out = check_out or data.get("check_out")
        
        if not all([user_id, hotel_id, room_type_id, check_in, check_out]):
            raise ValueError("Faltan datos para crear la reservación")
        
        print(f"[Integration] Creando reservación para user={user_id}")
        
        # Calcular total si no viene
        if total_price is None:
            calculated = Decimal(base_price) + Decimal(taxes) - Decimal(discounts)
            total_price = str(calculated)
        
        command = CreateReservationCommand(
            user_id=UUID(user_id),
            hotel_id=UUID(hotel_id),
            room_type_id=UUID(room_type_id),
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            base_price=Decimal(base_price),
            taxes=Decimal(taxes),
            discounts=Decimal(discounts),
            total_price=Decimal(total_price),
            special_requests=special_requests,
        )
        
        result = await self.mediator.send_async(command)
        
        # Guardar el ID de la reservación creada en el contexto
        self.set_context("reservation_id", str(result.id))
        self.set_context("confirmation_code", result.confirmation_code)
        
        print(f"[Integration] Reservación creada: {result.confirmation_code}")
        
        return result
    
    async def process_payment(self) -> Dict[str, Any]:
        """Procesa el pago (simulado)."""
        reservation_id = self.get_context("reservation_id")
        print(f"[Integration] Procesando pago para reservación {reservation_id}")
        
        return {
            "success": True,
            "payment_id": f"PAY-{reservation_id}",
            "message": "Pago procesado exitosamente"
        }
    
    # ========== FUNCIONES PARA ESTADO CANCELATION ==========
    
    async def cancel_reservation(self, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancela la reservación.
        Usa el reservation_id del contexto si no se pasa explícitamente.
        """
        reservation_id = self.get_context("reservation_id")
        
        if not reservation_id:
            raise ValueError("No hay reservación en el contexto para cancelar")
        
        print(f"[Integration] Cancelando reservación {reservation_id}")
        
        # Actualizar estado a cancelled
        command = UpdateReservationStatusCommand(
            reservation_id=UUID(reservation_id),
            status="cancelled"
        )
        
        result = await self.mediator.send_async(command)
        
        return {
            "success": True,
            "reservation_id": reservation_id,
            "previous_status": result.previous_status,
            "message": f"Reservación cancelada. Razón: {reason or 'No especificada'}"
        }
    
    async def cleanup_resources(self) -> Dict[str, Any]:
        """Limpia recursos asociados (simulado)."""
        reservation_id = self.get_context("reservation_id")
        print(f"[Integration] Limpiando recursos para reservación {reservation_id}")
        
        return {
            "success": True,
            "message": "Recursos liberados"
        }
    
    async def send_notification(self, message_type: str = "cancellation") -> Dict[str, Any]:
        """Envía notificación al usuario (simulado)."""
        reservation_id = self.get_context("reservation_id")
        print(f"[Integration] Enviando notificación {message_type} para reservación {reservation_id}")
        
        return {
            "success": True,
            "message": f"Notificación de {message_type} enviada"
        }
