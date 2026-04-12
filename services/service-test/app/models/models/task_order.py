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
    # Estados: validate, create, cancelation
    status: str = Field(default="validate")
    # Historial de estados en formato JSON string: ["validate", "create"]
    history: Optional[str] = Field(default='["validate"]')
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
