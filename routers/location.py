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
        <title>Моє місце знаходження</title>
    </head>

    <body>

        <h1>Визначення місця знаходження</h1>

        <button onclick="getLocation()">
            Визначити моє місце знаходження
        </button>

        <pre id="result"></pre>

        <script>

            function getLocation() {

                const result =
                    document.getElementById("result");

                result.textContent =
                    "Визначаємо місце знаходження...";

                if (!navigator.geolocation) {

                    result.textContent =
                        "Ваш браузер не підтримує Geolocation API";

                    return;
                }

                navigator.geolocation.getCurrentPosition(

                    function(position) {

                        const lat =
                            position.coords.latitude;

                        const lng =
                            position.coords.longitude;

                        // Зберегти координати в localStorage
                        localStorage.setItem(
                            "customer_lat",
                            lat
                        );

                        localStorage.setItem(
                            "customer_lng",
                            lng
                        );

                        // Визначення координат на FastAPI
                        fetch("/location/", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({
                                lat: lat,
                                lng: lng
                            })
                        })

                        .then(response => {

                            if (!response.ok) {
                                throw new Error(
                                    "Помилка HTTP: "
                                    + response.status
                                );
                            }

                            return response.json();
                        })

                        .then(data => {

                            result.textContent =
                                "Широта: "
                                + data.lat
                                + "\\n"
                                + "Довгота: "
                                + data.lng
                                + "\\n\\n"
                                + data.message;
                        })

                        .catch(error => {

                            result.textContent =
                                "GPS отримано, "
                                + "але координати не вдалося "
                                + "відправити на сервер.\\n\\n"
                                + "Широта: "
                                + lat
                                + "\\n"
                                + "Долгота: "
                                + lng
                                + "\\n\\n"
                                + "помилка: "
                                + error.message;
                        });
                    },

                    function(error) {

                        result.textContent =
                            "Не вдалося визначити місце знаходження: "
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
        "message": "Координати отримано сервером",
        "lat": location.lat,
        "lng": location.lng
    }
