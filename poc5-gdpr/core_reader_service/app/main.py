"""
Reader service: runs the RabbitMQ consumer (CQRS read model updater).
"""
from .consumer import run_consumer

if __name__ == "__main__":
    run_consumer()
