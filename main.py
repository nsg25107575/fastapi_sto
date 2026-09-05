from dotenv import load_dotenv
from fastapi import FastAPI
from routers.location import router as location_router
from models.station_contact import StationContactModel
from models.station_service import StationServiceModel

load_dotenv()

from routers import stations

app = FastAPI()

app.include_router(
    stations.router,
    prefix="/stations"
)

app.include_router(location_router)
