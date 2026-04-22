import os
import resend
from typing import Optional
from pydantic import BaseModel

from fastapi import Header, HTTPException, status, Depends
from notification_service.email_handler import send_email_notification

from fastapi import APIRouter

token_resend = os.environ["RESEND_API_KEY"]
resend.api_key = token_resend


router = APIRouter(prefix="/notification", tags=["notification"])

def verify_api_token(x_api_token: str = Header(...)):
    if x_api_token != token_resend:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Token"
        )


class Email(BaseModel):
    email: str
    message: Optional[str]

@router.post("/send-email", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_token)])
async def send_email(data_email: Email):
    send_email_notification(data_email.email, data_email.message)

