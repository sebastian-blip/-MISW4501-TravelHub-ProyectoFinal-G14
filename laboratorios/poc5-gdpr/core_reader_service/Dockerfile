FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY core_reader_service/ ./core_reader_service/

CMD ["python", "-m", "core_reader_service.app.main"]
