"""
Router para máquina de estados flexible con pasos numéricos (1-4).
Permite saltar entre cualquier paso y mantiene historial.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from pydantic import BaseModel

from infrastructure.database import get_session
from domain.models.task_order import TaskOrder
from state_machine import TaskStateMachine, STEP_NAMES

router = APIRouter(prefix="/tasks", tags=["State Machine"])


# Schemas Pydantic
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    step: int
    step_name: str
    history: List[int]
    created_at: datetime
    updated_at: Optional[datetime]
    available_jumps: List[int]

    class Config:
        from_attributes = True


class JumpRequest(BaseModel):
    """Request para saltar a un paso específico (1-4)"""
    target_step: int  # 1, 2, 3, o 4


class JumpResponse(BaseModel):
    success: bool
    previous_step: int
    new_step: int
    history: List[int]
    message: str


class GoBackResponse(BaseModel):
    success: bool
    previous_step: int
    new_step: int
    history: List[int]
    message: str


def parse_history(history_json: Optional[str]) -> List[int]:
    """Parsea el historial desde JSON string."""
    return TaskStateMachine.parse_history(history_json or "[]")


@router.post("", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    session: AsyncSession = Depends(get_session)
):
    """Crea una nueva tarea iniciando en paso 1."""
    sm = TaskStateMachine(initial_step=1)
    
    task = TaskOrder(
        title=task_data.title,
        description=task_data.description,
        status=1,
        history=sm.get_history_json()
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        step=sm.step,
        step_name=sm.state,
        history=sm.history,
        created_at=task.created_at,
        updated_at=task.updated_at,
        available_jumps=sm.get_available_transitions()
    )


@router.get("", response_model=List[TaskResponse])
async def list_tasks(session: AsyncSession = Depends(get_session)):
    """Lista todas las tareas con su historial."""
    result_query = await session.exec(select(TaskOrder))
    tasks = result_query.all()
    result = []
    for task in tasks:
        history = parse_history(task.history)
        sm = TaskStateMachine(initial_step=task.status, history=history)
        result.append(TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            step=sm.step,
            step_name=sm.state,
            history=history,
            created_at=task.created_at,
            updated_at=task.updated_at,
            available_jumps=sm.get_available_transitions()
        ))
    return result


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)):
    """Obtiene una tarea específica con su historial."""
    task = await session.get(TaskOrder, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    history = parse_history(task.history)
    sm = TaskStateMachine(initial_step=task.status, history=history)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        step=sm.step,
        step_name=sm.state,
        history=history,
        created_at=task.created_at,
        updated_at=task.updated_at,
        available_jumps=sm.get_available_transitions()
    )


@router.post("/{task_id}/jump", response_model=JumpResponse)
async def jump_to_step(
    task_id: int,
    jump_request: JumpRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Salta a cualquier paso (1-4) directamente.
    """
    task = await session.get(TaskOrder, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Validar paso destino
    if jump_request.target_step not in [1, 2, 3, 4]:
        raise HTTPException(
            status_code=400,
            detail=f"Paso '{jump_request.target_step}' no válido. Use 1, 2, 3 o 4"
        )
    
    # Crear máquina de estados con el historial actual
    history = parse_history(task.history)
    sm = TaskStateMachine(initial_step=task.status, history=history)
    
    # Ejecutar salto
    previous_step = sm.step
    success = sm.jump_to(jump_request.target_step)
    
    if not success:
        return JumpResponse(
            success=False,
            previous_step=previous_step,
            new_step=sm.step,
            history=sm.history,
            message=f"Ya estás en el paso {jump_request.target_step}"
        )
    
    # Actualizar en base de datos
    task.status = sm.step
    task.history = sm.get_history_json()
    task.updated_at = datetime.utcnow()
    
    session.add(task)
    await session.commit()
    
    return JumpResponse(
        success=True,
        previous_step=previous_step,
        new_step=sm.step,
        history=sm.history,
        message=f"Salto exitoso: paso {previous_step} → paso {sm.step}"
    )


@router.post("/{task_id}/go-back", response_model=GoBackResponse)
async def go_back(
    task_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Retrocede al paso anterior en el historial.
    """
    task = await session.get(TaskOrder, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Crear máquina de estados con el historial actual
    history = parse_history(task.history)
    sm = TaskStateMachine(initial_step=task.status, history=history)
    
    # Intentar retroceder
    previous_step = sm.step
    success = sm.go_back()
    
    if not success:
        return GoBackResponse(
            success=False,
            previous_step=previous_step,
            new_step=sm.step,
            history=sm.history,
            message="No hay pasos anteriores en el historial"
        )
    
    # Actualizar en base de datos
    task.status = sm.step
    task.history = sm.get_history_json()
    task.updated_at = datetime.utcnow()
    
    session.add(task)
    await session.commit()
    
    return GoBackResponse(
        success=True,
        previous_step=previous_step,
        new_step=sm.step,
        history=sm.history,
        message=f"Retroceso exitoso: paso {previous_step} → paso {sm.step}"
    )


@router.get("/diagram/state-machine-info")
async def get_state_machine_info():
    """Retorna información sobre la máquina de estados."""
    return {
        "steps": {
            1: "step_one",
            2: "step_two",
            3: "step_three",
            4: "step_four"
        },
        "description": "Máquina de estados flexible con historial de navegación",
        "features": [
            "Salto directo a cualquier paso (1-4)",
            "Retroceso al paso anterior",
            "Historial de pasos visitados"
        ],
        "endpoints": {
            "POST /tasks/{id}/jump": "Salta a un paso específico (1, 2, 3, 4)",
            "POST /tasks/{id}/go-back": "Retrocede al paso anterior en el historial"
        }
    }
