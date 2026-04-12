import datetime
import uuid
from typing import Optional

from sqlmodel import Field, SQLModel


class PmsSyncLog(SQLModel, table=True):
    __tablename__ = "pms_sync_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hotel_id: uuid.UUID
    pms_provider: str = Field(max_length=100)
    sync_type: str = Field(max_length=50)
    status: str = Field(max_length=50)
    records_synced: int = Field(default=0)
    error_message: Optional[str] = Field(default=None)
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = Field(default=None)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
