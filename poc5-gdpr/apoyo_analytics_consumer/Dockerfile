FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY apoyo_analytics_consumer/ ./apoyo_analytics_consumer/

CMD ["python", "-m", "apoyo_analytics_consumer.app.main"]
