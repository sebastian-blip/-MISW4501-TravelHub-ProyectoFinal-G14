import json
from datetime import date, datetime

def _serialize(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class EventMachine:

    def __init__(self, wait_for_reply, async_session_maker):

        self.wait_for_reply = wait_for_reply
        self.async_session_maker = async_session_maker

    async def validate_reservation(self, publish_reservation_validate, correlation_id, user_id, hotel_id, room_type_id, check_in, check_out):
        try:
            await publish_reservation_validate(
                user_id=user_id,
                hotel_id=hotel_id,
                room_type_id=room_type_id,
                check_in=check_in.isoformat() if isinstance(check_in, date) else str(check_in),
                check_out=check_out.isoformat() if isinstance(check_out, date) else str(check_out),
                correlation_id=correlation_id
            )

            result = await self.wait_for_reply(correlation_id, timeout=5.0)

            exists = result.get("exists", False)
            if exists:
                msg = result.get("message", "")
                return {
                    "success": True,
                    "proceed": False,
                    "exists": True,
                    "from_kafka": True,
                    "message": str(msg).strip() or "Reserva ya existe, no se puede crear."
                }
            else:
                return {
                    "success": True,
                    "proceed": True,   # ← fix: si no existe, sí proceder
                    "exists": False,
                    "from_kafka": True,
                    "message": "No existe reserva. OK para crear."
                }

        except TimeoutError:
            print("[EventMachine] Timeout esperando respuesta Kafka")
            return None
        except Exception as e:
            print(f"[EventMachine] Error: {e}")
            return None