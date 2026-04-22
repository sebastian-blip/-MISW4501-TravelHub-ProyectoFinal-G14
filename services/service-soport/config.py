from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    TOKEN_SOPORT_SERVICES = os.getenv("TOKEN_SOPORT_SERVICES")

settings = Settings()