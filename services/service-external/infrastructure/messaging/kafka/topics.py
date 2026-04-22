# Must match service-core:
# - producer: services/service-core/infrastructure/messaging/kafka/producer.py (TOPIC_RESERVATION_VALIDATE)
# - reply consumer: services/service-core/infrastructure/messaging/kafka/reply_consumer.py (TOPIC_RESERVATION_RESULTS)
TOPIC_RESERVATION_VALIDATE = "reservation-validate-requests"
TOPIC_RESERVATION_RESULTS = "reservation-validate-results"
