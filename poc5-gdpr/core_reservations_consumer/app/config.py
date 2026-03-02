import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:postgres@localhost:5433/poc5_gdpr")
AUDIT_DATABASE_URL = os.getenv("AUDIT_DATABASE_URL", DATABASE_URL)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
CONSUMER_ID = "reservations"

# UUID usado como user_id anónimo en reservas históricas (integridad referencial)
ANONYMOUS_USER_ID = "00000000-0000-0000-0000-000000000001"
