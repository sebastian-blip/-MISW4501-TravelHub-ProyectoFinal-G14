import os

DB_API_URL = os.getenv("DB_API_URL", "http://localhost:8080")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CONSUMER_ID = "analytics"
ANONYMOUS_USER_ID = os.getenv("ANONYMOUS_USER_ID", "00000000-0000-0000-0000-000000000001")
DELAY_ANALYTICS_SEC = int(os.environ.get("DELAY_ANALYTICS_SEC", "0"))
