import os

DB_API_URL = os.getenv("DB_API_URL", "http://localhost:8080")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
