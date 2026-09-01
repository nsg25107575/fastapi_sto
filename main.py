from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()  # Load environment variables from .env file

from database import engine
from models.station import Base
from routers import stations

# Create the database tables
Base.metadata.create_all(bind=engine)
app = FastAPI()


# Include the stations router
app.include_router(
    stations.router,
    prefix="/stations"
)
