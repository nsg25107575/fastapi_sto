from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

router = APIRouter(
    prefix="/location",
    tags=["Location"]
)


class Location(BaseModel):
    lat: float
    lng: float


@router.get("/", response_class=HTMLResponse)
def location_page():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Моё местоположение</title>
    </head>

    <body>

        <h1>Определение местоположения</h1>

        <button onclick="getLocation()">
            Определить моё местоположение
        </button>

        <p id="result"></p>

        <script>

            async function getLocation() {

                const result = document.getElementById("result");

                result.textContent = "Определяем местоположение...";

                if (!navigator.geolocation) {
                    result.textContent =
                        "Ваш браузер не поддерживает Geolocation API";
                    return;
                }

                navigator.geolocation.getCurrentPosition(

                    async function(position) {

                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;

                        result.textContent =
                            `Широта: ${lat}, Долгота: ${lng}`;

                        const response = await fetch("/location/", {
                            method: "POST",

                            headers: {
                                "Content-Type": "application/json"
                            },

                            body: JSON.stringify({
                                lat: lat,
                                lng: lng
                            })
                        });

                        const data = await response.json();

                        console.log(data);
                    },

                    function(error) {

                        result.textContent =
                            "Не удалось определить местоположение: "
                            + error.message;
                    }
                );
            }

        </script>

    </body>
    </html>
    """


@router.post("/")
def receive_location(location: Location):
    return {
        "message": "Координаты получены",
        "lat": location.lat,
        "lng": location.lng
    }
