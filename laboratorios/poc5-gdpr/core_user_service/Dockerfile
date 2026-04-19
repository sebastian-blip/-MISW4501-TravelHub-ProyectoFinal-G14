FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY core_user_service/ ./core_user_service/

EXPOSE 8000
CMD ["uvicorn", "core_user_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
