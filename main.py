from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from routers import stations
from routers.auth import router as auth_router
from routers.customer import router as customer_router
from routers.location import router as location_router

load_dotenv()

app = FastAPI(
    docs_url=None
)

app.include_router(
    stations.router,
    prefix="/stations"
)

app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(location_router)


@app.get("/docs", include_in_schema=False)
async def custom_docs():
    return HTMLResponse(
        f"""
<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <title>FastAPI Swagger</title>

    <link
        rel="stylesheet"
        type="text/css"
        href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
    >

</head>

<body>

<div id="swagger-ui"></div>


<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>

<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>


<script>

window.onload = function(){{

    SwaggerUIBundle({{

        url: "{app.openapi_url}",

        dom_id: "#swagger-ui",

        deepLinking: true,

        presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIStandalonePreset
        ],

        layout: "StandaloneLayout"

    }});


    function fillCustomerCoordinates(){{

        const lat =
            localStorage.getItem("customer_lat");

        const lng =
            localStorage.getItem("customer_lng");


        if (lat === null || lng === null) {{
            return;
        }}


        const textareas =
            document.querySelectorAll("textarea");


        textareas.forEach(function(textarea){{

            try {{

                const body =
                    JSON.parse(textarea.value);


                // Перевіряємо, чи є JSON поля "lat" та "lng"

                if (
                    body &&
                    Object.prototype.hasOwnProperty.call(
                        body,
                        "lat"
                    ) &&
                    Object.prototype.hasOwnProperty.call(
                        body,
                        "lng"
                    )
                ) {{

                    // Координати записуються в Swagger UI

                    body.lat = Number(lat);
                    body.lng = Number(lng);


                    const newValue =
                        JSON.stringify(
                            body,
                            null,
                            2
                        );


                    if (
                        textarea.value !== newValue
                    ) {{

                        const setter =
                            Object.getOwnPropertyDescriptor(
                                HTMLTextAreaElement.prototype,
                                "value"
                            ).set;


                        setter.call(
                            textarea,
                            newValue
                        );


                        textarea.dispatchEvent(
                            new Event(
                                "input",
                                {{
                                    bubbles: true
                                }}
                            )
                        );


                        textarea.dispatchEvent(
                            new Event(
                                "change",
                                {{
                                    bubbles: true
                                }}
                            )
                        );

                    }}

                }}

            }} catch (error) {{

                // Текстовое поле может содержать не JSON.
                // В этом случае ничего не делаем.

            }}

        }});

    }}


    const observer =
        new MutationObserver(
            function(){{

                fillCustomerCoordinates();

            }}
        );


    observer.observe(
        document.body,
        {{
            childList: true,
            subtree: true
        }}
    );


    setInterval(
        fillCustomerCoordinates,
        500
    );

}};

</script>


</body>

</html>
"""
    )