from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    TOKEN_SOPORT_SERVICES = os.getenv("TOKEN_SOPORT_SERVICES")
    URL_CORE_SERVICE = os.getenv("URL_CORE_SERVICE", 'http://service-core:80')

settings = Settings()