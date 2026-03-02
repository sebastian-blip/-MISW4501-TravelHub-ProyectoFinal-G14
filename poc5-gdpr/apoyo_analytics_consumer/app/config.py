import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:postgres@localhost:5433/poc5_gdpr")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
CONSUMER_ID = "analytics"
