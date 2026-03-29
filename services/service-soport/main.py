import os

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI(
    title="TravelHub API",
    version="0.1.0",
)


@app.get("/healthz", tags=["health"], include_in_schema=False)
def healthz():
    return {"status": "ok"}

# Readiness: listo para recibir tráfico (aquí puedes validar dependencias)
@app.get("/readyz", tags=["health"], include_in_schema=False)
def readyz():
    # Ejemplo simple: siempre listo.
    # Aquí normalmente validarías DB/Redis/broker, etc. y si falla:
    # return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"status": "not_ready"})
    bd = os.getenv("POSTGRES_HOST")
    return {"status": bd}

