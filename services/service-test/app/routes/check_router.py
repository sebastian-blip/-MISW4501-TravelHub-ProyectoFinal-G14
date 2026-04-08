from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.infrastructure.database import get_session
from app.models.models.task_order import TaskOrder
from app.models.models.user import User
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


# Ejemplo de endpoints usando la base de datos
@router.get("/tasks", tags=["Database Example"])
async def list_tasks(session: AsyncSession = Depends(get_session)):
    """Lista todas las tareas desde la base de datos."""
    from sqlalchemy import select
    result = await session.execute(select(TaskOrder))
    tasks = result.scalars().all()
    return {"tasks": tasks}


@router.get("/tasks/{task_id}", tags=["Database Example"])
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)):
    """Obtiene una tarea específica por ID."""
    task = await session.get(TaskOrder, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return task


@router.get("/db-check", tags=["Database Check"])
async def check_db_connection(session: AsyncSession = Depends(get_session)):
    """Verifica que la conexión a la base de datos funcione consultando usuarios."""
    try:
        from sqlalchemy import select
        result = await session.execute(select(User))
        users = result.scalars().all()
        return {
            "status": "ok",
            "connected": True,
            "total_users": len(users),
            "sample_users": [u.email for u in users[:5]]  # Primeros 5 emails
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")
