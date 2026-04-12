from sqlmodel import Field, SQLModel
from sqlalchemy import JSON
from typing import Optional, Dict, Any
import datetime
import uuid


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None)
    action: str = Field(max_length=100)
    entity_type: Optional[str] = Field(default=None, max_length=50)
    entity_id: Optional[uuid.UUID] = Field(default=None)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    details: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def __str__(self):
        return f"{self.action} - {self.entity_type}"
