from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class TaskOrder(SQLModel, table=True):
    __tablename__ = "task_orders"
    
    id: Optional[int] = Field(
        default=None, 
        primary_key=True,
        sa_column_kwargs={"autoincrement": True}
    )
    title: str = Field(index=True)
    description: Optional[str] = None
    # Estado numérico: 1=step_one, 2=step_two, 3=step_three, 4=step_four
    status: int = Field(default=1)
    # Historial de estados en formato JSON string: [1, 2, 3]
    history: Optional[str] = Field(default="[1]")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
