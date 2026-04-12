FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY core_reservations_consumer/ ./core_reservations_consumer/

CMD ["python", "-m", "core_reservations_consumer.app.main"]
