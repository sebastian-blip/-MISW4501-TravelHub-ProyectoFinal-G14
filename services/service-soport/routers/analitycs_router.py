import resend
import requests
from datetime import date

from fastapi import HTTPException, status, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import APIRouter
from config import settings
from fastapi.responses import JSONResponse


from analytics_service.hotel_admin_dashboard import bookings_stats

security = HTTPBearer()


router = APIRouter(prefix="/analitycs", tags=["analitycs"])

@router.get("/dahsboard", status_code=status.HTTP_200_OK)
async def dashboard(
        start_date: date = Query(..., description="Fecha de inicio del rango"),
        end_date: date = Query(..., description="Fecha de fin del rango"),
        credentials: HTTPAuthorizationCredentials = Depends(security)):

    try:

        url = f'{settings.URL_CORE_SERVICE}/hotel-admin/reservations?start_date={start_date}&end_date={end_date}'
        headers = {"Authorization": f"Bearer {credentials.credentials}"}
        response = requests.get(url, headers=headers)
        reservations_stats = []

        if response.status_code != 200:
            return JSONResponse(status_code=response.status_code, content=response.json())
        data = response.json().get('items')
        if data:
            reservations_stats = bookings_stats(data)
        return JSONResponse(status_code=status.HTTP_200_OK, content=reservations_stats)

    except Exception as e:
        return JSONResponse(status_code=500, content='Internal Server Error')






