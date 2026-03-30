FROM python:3.11-slim
WORKDIR /app
COPY libs/service_external /app/service_external
COPY services/service-external/payment/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY services/service-external/payment/app /app/app
ENV PYTHONPATH=/app
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
