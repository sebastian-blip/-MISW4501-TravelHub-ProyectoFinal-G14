"""
Router para máquina de estados con Meta y estados nombrados.
Estados: validate → create → cancelation
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from pydantic import BaseModel

from infrastructure.database import get_session
from infrastructure.messaging.kafka.producer import publish_step_change
from domain.models.task_order import TaskOrder
from state_machine import TaskStateMachine, Meta

router = APIRouter(prefix="/tasks", tags=["State Machine"])


# Schemas Pydantic
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    state: str
    state_description: str
    history: List[str]
    available_functions: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    available_transitions: List[str]

    class Config:
        from_attributes = True


class TransitionRequest(BaseModel):
    """Request para transicionar a un estado específico"""
    target_state: str  # "validate", "create", "cancelation"


class ExecuteFunctionRequest(BaseModel):
    """Request para ejecutar una función del estado actual"""
    function_name: str  # "check_user_exists", "save_to_database", etc.


class TransitionResponse(BaseModel):
    success: bool
    previous_state: str
    new_state: str
    history: List[str]
    available_functions: List[str]
    message: str


class FunctionResponse(BaseModel):
    success: bool
    state: str
    function_executed: str
    available_functions: List[str]
    message: str


def parse_history(history_json: Optional[str]) -> List[str]:
    """Parsea el historial desde JSON string."""
    return TaskStateMachine.parse_history(history_json or "[]")


@router.post("", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    session: AsyncSession = Depends(get_session)
):
    """Crea una nueva tarea iniciando en estado 'validate'."""
    sm = TaskStateMachine(initial_state=Meta.VALIDATE)
    
    task = TaskOrder(
        title=task_data.title,
        description=task_data.description,
        status=Meta.VALIDATE,
        history=sm.get_history_json()
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        state=sm.state,
        state_description=sm.get_description(),
        history=sm.history,
        available_functions=sm.get_available_functions(),
        created_at=task.created_at,
        updated_at=task.updated_at,
        available_transitions=sm.get_available_transitions()
    )


@router.get("", response_model=List[TaskResponse])
async def list_tasks(session: AsyncSession = Depends(get_session)):
    """Lista todas las tareas con su historial."""
    result_query = await session.execute(select(TaskOrder))
    tasks = result_query.scalars().all()
    result = []
    for task in tasks:
        history = parse_history(task.history)
        sm = TaskStateMachine(initial_state=task.status, history=history)
        result.append(TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            state=sm.state,
            state_description=sm.get_description(),
            history=history,
            available_functions=sm.get_available_functions(),
            created_at=task.created_at,
            updated_at=task.updated_at,
            available_transitions=sm.get_available_transitions()
        ))
    return result


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)):
    """Obtiene una tarea específica con su historial."""
    task = await session.get(TaskOrder, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    history = parse_history(task.history)
    sm = TaskStateMachine(initial_state=task.status, history=history)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        state=sm.state,
        state_description=sm.get_description(),
        history=history,
        available_functions=sm.get_available_functions(),
        created_at=task.created_at,
        updated_at=task.updated_at,
        available_transitions=sm.get_available_transitions()
    )


@router.post("/{task_id}/transition", response_model=TransitionResponse)
async def transition_to_state(
    task_id: int,
    transition_request: TransitionRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Transiciona a cualquier estado (validate, create, cancelation).
    """
    task = await session.get(TaskOrder, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Validar estado destino
    target = transition_request.target_state.lower()
    if target not in Meta.ALL_STATES:
        raise HTTPException(
            status_code=400,
            detail=f"Estado '{target}' no válido. Use: {Meta.ALL_STATES}"
        )
    
    # Crear máquina de estados con el historial actual
    history = parse_history(task.history)
    sm = TaskStateMachine(initial_state=task.status, history=history)
    
    # Ejecutar transición (ahora permite re-ejecutar el mismo estado)
    previous_state = sm.state
    sm.transition_to(target)
    
    # Actualizar en base de datos
    task.status = sm.state
    task.history = sm.get_history_json()
    task.updated_at = datetime.utcnow()
    
    session.add(task)
    await session.commit()
    
    # Emitir evento Kafka (usando el step numérico para compatibilidad o el nombre)
    try:
        # Mapear estado a número para el evento Kafka si es necesario
        state_to_num = {Meta.VALIDATE: 1, Meta.CREATE: 2, Meta.CANCELATION: 3}
        await publish_step_change(
            task_id, 
            state_to_num.get(previous_state, 0), 
            state_to_num.get(sm.state, 0),
            sm.history
        )
    except Exception as e:
        print(f"[Warning] No se pudo enviar evento Kafka: {e}")
    
    # Determinar mensaje según si fue transición o re-ejecución
    if previous_state == sm.state:
        message = f"Re-ejecución de estado '{sm.state}' exitosa"
    else:
        message = f"Transición exitosa: '{previous_state}' → '{sm.state}'"
    
    return TransitionResponse(
        success=True,
        previous_state=previous_state,
        new_state=sm.state,
        history=sm.history,
        available_functions=sm.get_available_functions(),
        message=message
    )


@router.post("/{task_id}/execute", response_model=FunctionResponse)
async def execute_state_function(
    task_id: int,
    function_request: ExecuteFunctionRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Ejecuta una función del estado actual.
    
    Funciones por estado:
    - validate: check_user_exists, verify_permissions
    - create: save_to_database, process_data
    - cancelation: cleanup_resources, send_notification
    """
    task = await session.get(TaskOrder, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Crear máquina de estados
    history = parse_history(task.history)
    sm = TaskStateMachine(initial_state=task.status, history=history)
    
    # Verificar que la función esté disponible
    available = sm.get_available_functions()
    if function_request.function_name not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Función '{function_request.function_name}' no disponible en estado '{sm.state}'. "
                   f"Funciones disponibles: {available}"
        )
    
    # Ejecutar función
    success = sm.execute_function(function_request.function_name)
    
    return FunctionResponse(
        success=success,
        state=sm.state,
        function_executed=function_request.function_name,
        available_functions=sm.get_available_functions(),
        message=f"Función '{function_request.function_name}' ejecutada en estado '{sm.state}'"
    )


@router.post("/{task_id}/go-back", response_model=TransitionResponse)
async def go_back(
    task_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Retrocede al estado anterior en el historial."""
    task = await session.get(TaskOrder, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    history = parse_history(task.history)
    sm = TaskStateMachine(initial_state=task.status, history=history)
    
    previous_state = sm.state
    success = sm.go_back()
    
    if not success:
        return TransitionResponse(
            success=False,
            previous_state=previous_state,
            new_state=sm.state,
            history=sm.history,
            available_functions=sm.get_available_functions(),
            message="No hay estados anteriores en el historial"
        )
    
    # Actualizar en base de datos
    task.status = sm.state
    task.history = sm.get_history_json()
    task.updated_at = datetime.utcnow()
    
    session.add(task)
    await session.commit()
    
    return TransitionResponse(
        success=True,
        previous_state=previous_state,
        new_state=sm.state,
        history=sm.history,
        available_functions=sm.get_available_functions(),
        message=f"Retroceso exitoso: '{previous_state}' → '{sm.state}'"
    )


@router.get("/meta/state-machine-info")
async def get_state_machine_info():
    """Retorna información sobre la máquina de estados (Meta)."""
    return {
        "meta": {
            "states": Meta.ALL_STATES,
            "descriptions": Meta.DESCRIPTIONS,
            "functions": Meta.FUNCTIONS
        },
        "transitions": {
            "validate": ["create", "cancelation"],
            "create": ["validate", "cancelation"],
            "cancelation": ["validate", "create"]
        },
        "description": "Máquina de estados con Meta-clase y estados nombrados",
        "features": [
            "Saltos entre cualquier estado",
            "Funciones asociadas por estado",
            "Historial de navegación",
            "Callbacks on_enter/on_exit"
        ]
    }
