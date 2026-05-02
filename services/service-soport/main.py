import os
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from routers.notification_router import router as notcation_router
from routers.analitycs_router import router as anatics_router




app = FastAPI(
    title="TravelHub API",
    version="0.1.1",
    root_path="/service-soport"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz", tags=["health"], include_in_schema=False)
def healthz():
    return {"status": "ok"}

# Readiness: listo para recibir tráfico (aquí puedes validar dependencias)
@app.get("/readyz", tags=["health"], include_in_schema=False)
def readyz():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ready"})


@app.get('/version', tags=["version"], include_in_schema=False)
def version():
    return {"version": app.version}


app.include_router(notcation_router)
app.include_router(anatics_router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)