from dotenv import load_dotenv
load_dotenv()
import resend
import os
from typing import Optional
from pydantic import BaseModel

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from notification_service.email_handler import send_email_notification

from fastapi import APIRouter

resend.api_key = os.getenv("RESEND_API_KEY")
API_BEARER_TOKEN = os.getenv("TOKEN_SOPORT_SERVICES")
security = HTTPBearer()


router = APIRouter(prefix="/notification", tags=["notification"])


def verify_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if credentials.scheme != "Bearer" or credentials.credentials != API_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Bearer Token"
        )

class Email(BaseModel):
    email: str
    message: Optional[str]

@router.post("/send-email", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_bearer_token)])
async def send_email(data_email: Email):
    send_email_notification(data_email.email, data_email.message)

