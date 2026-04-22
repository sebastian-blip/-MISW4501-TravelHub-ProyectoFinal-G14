import os
import resend
from typing import Optional
from pydantic import BaseModel

from starlette import status
from notification_service.email_handler import send_email_notification

from fastapi import APIRouter
resend.api_key = os.environ["RESEND_API_KEY"]


router = APIRouter(prefix="/notification", tags=["notification"])


class Email(BaseModel):
    email: str
    message: Optional[str]

@router.post("/send-email", status_code=status.HTTP_201_CREATED)
async def send_email(data_email: Email):
    send_email_notification(data_email.email, data_email.message)

