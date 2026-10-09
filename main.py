import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from starlette.requests import Request
from starlette.responses import JSONResponse

from config import Config
from exceptions.exceptions import app_not_found_exception
from i18n.context import set_current_locale
from i18n.dependency import get_locale
from i18n.dependency_translator import t
from routers.auth import router as auth_router
from routers.chat import router as chat_router
from routers.customer import router as customer_router
from routers.order import router as order_router
from routers.review import router as review_router
from routers.service import router as service_router
from routers.stations import router as station_router

load_dotenv()

app = FastAPI(
    docs_url=None
)

app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(station_router)
app.include_router(order_router)
app.include_router(review_router)
app.include_router(service_router)
app.include_router(chat_router)

# Lock down the interactive schema/docs endpoints outside local
# development. Checked at REQUEST time (not import/startup time) against
# Config.app_env, so tests can flip it per-test via monkeypatch and a
# running process reflects an APP_ENV change without needing a restart
# to verify it. Default-deny: anything other than the literal string
# "development" is blocked -- an unset/misconfigured APP_ENV in
# production fails safe (blocked) instead of failing open (exposed),
# which is what happened at sto.kirweb.space/docs prior to this fix.
@app.middleware("http")
async def block_schema_endpoints_outside_dev(request: Request, call_next):
    set_current_locale(get_locale(request))

    if request.url.path == "/openapi.json" and Config.app_env != "development":
        return JSONResponse(status_code=404, content={"detail": t("app.not_found")})

    return await call_next(request)


@app.get("/docs", include_in_schema=False)
async def custom_docs():
    if Config.app_env != "development":
        raise app_not_found_exception()

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

window.onload = () => {{
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
}};

function fillSwaggerDataForCustomerData() {{
    const customer = {{
        device_hash: localStorage.getItem("device_hash") ?? null,
        public_ip: localStorage.getItem("user_public_ip") ?? null,
        public_data: localStorage.getItem("user_public_data") ?? null,
        coordinates: {{
            lat: localStorage.getItem("lat") || null,
            lng: localStorage.getItem("lng") || null,
        }},
    }};
    
    if (customer.device_hash === null) {{
        return;
    }}
    
    const t = document.querySelectorAll("textarea");
    
    t.forEach(
        (textarea) => {{
            try {{
                const value = JSON.parse(textarea.value);
                if (value 
                    && Object.prototype.hasOwnProperty.call(value,"device_hash")
                    && Object.prototype.hasOwnProperty.call(value,"ip")
                    && Object.prototype.hasOwnProperty.call(value,"lat") 
                    && Object.prototype.hasOwnProperty.call(value,"lng")) {{
                        value.device_hash = customer.device_hash;
                        value.ip = customer.public_ip;
                        value.lat = Number(customer.coordinates.lat);
                        value.lng = Number(customer.coordinates.lng);
                        
                        const newValue = JSON.stringify(value);
                         if (textarea.value !== newValue) {{
                            const setter = Object.getOwnPropertyDescriptor(
                                HTMLTextAreaElement.prototype, "value"
                            ).set;
                            
                            setter.call(textarea, newValue);
                            
                            // Re-create "input" event
                            textarea.dispatchEvent(new Event("input",{{bubbles: true}}));
                            // Re-create "change" event 
                            textarea.dispatchEvent(new Event("change",{{bubbles: true}}));
                         }}
                }}
            }} catch (error) {{
                // Textarea tag hasn't contains a JSON string
                // Nothing to do!
            }}
        }}
    );
}}


function setInputValue(input, value) {{
    const setter =
        Object.getOwnPropertyDescriptor(
            HTMLInputElement.prototype,
            "value"
        ).set;

    setter.call(input, value);

    input.dispatchEvent(
        new Event("input", {{ bubbles: true }})
    );

    input.dispatchEvent(
        new Event("change", {{ bubbles: true }})
    );
}}

function fillNearestStationsParameters() {{
    const lat = localStorage.getItem("lat");
    const lng = localStorage.getItem("lng");

    if (lat === null || lng === null) {{
        return;
    }}

    const latInput =
        document.querySelector('input[placeholder="lat"]');

    const lngInput =
        document.querySelector('input[placeholder="lng"]');

    if (latInput && latInput.value !== lat) {{
        setInputValue(latInput, lat);
    }}

    if (lngInput && lngInput.value !== lng) {{
        setInputValue(lngInput, lng);
    }}
}}

document.addEventListener('DOMContentLoaded', () => {{
    const swaggerContainer = document.getElementById("swagger-ui");

    if (swaggerContainer) {{
        swaggerContainer.addEventListener("click", (e) => {{
            const targetLink = e.target.closest("#customer-data-link");

            if (targetLink) {{
                e.preventDefault();

                const linkHref = targetLink.getAttribute("href");

                const newWindow = window.open(
                    linkHref,
                    "_blank",
                    "width=100,height=100"
                );

                const checkStorageInterval = setInterval(() => {{
                    if (
                        localStorage.getItem("device_hash") !== null &&
                        localStorage.getItem("user_public_ip") !== null &&
                        localStorage.getItem("lat") !== null &&
                        localStorage.getItem("lng") !== null
                    ) {{
                        clearInterval(checkStorageInterval);

                        if (newWindow && !newWindow.closed) {{
                            newWindow.close();
                        }}
                    }}
                }}, 50);
            }}
        }});
    }}
    const observer = new MutationObserver(() => {{
        fillSwaggerDataForCustomerData();
        fillNearestStationsParameters();
    }});

    observer.observe(document.body, {{
        childList: true,
        subtree: true
    }});
    fillSwaggerDataForCustomerData();
    fillNearestStationsParameters();
}});

</script>

</body>
</html>
""")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
