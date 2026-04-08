from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.kafka.producer import publish_user_check
from app.kafka.consumer import results

router = APIRouter(prefix="/validate", tags=["Validate"])


class CheckUserRequest(BaseModel):
    email: str


@router.post("/user")
async def validate_user(body: CheckUserRequest):
    """Publica un evento Kafka para validar si el usuario existe."""
    await publish_user_check(body.email)
    return {
        "status": "publicado",
        "message": f"Evento enviado a Kafka para validar '{body.email}'",
    }


@router.get("/results")
async def get_results():
    """Retorna todos los resultados procesados por el consumer."""
    return {
        "total": len(results),
        "results": results,
    }