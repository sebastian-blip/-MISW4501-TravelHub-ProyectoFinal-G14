FROM python:3.12-slim

WORKDIR /app

# Crear directorio para certificados
RUN mkdir -p /app/certs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Si existe un certificado en /service, copiarlo también (para compatibilidad)
RUN if [ -d /service ]; then cp /service/*.pem /app/certs/ 2>/dev/null || true; fi

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
