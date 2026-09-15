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
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>GeoLocation API</title>
    </head>
    <body>
        <script>
            const lS = localStorage;
                        
            // Generate device hash
            const generateDeviceHash = () => {
                //Timestamp
                let dt = new Date().getTime();
                //Time in microseconds since page-load or 0 if unsupported
                let dt2 = ((typeof performance !== 'undefined') && performance.now && (performance.now() * 1000)) || 0;
                return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                    let rd = Math.random() * 16; //random number between 0 and 16
                    if(dt > 0) { //Use timestamp until depleted
                        rd = (dt + rd) % 16 | 0;
                        dt = Math.floor(dt / 16);
                    } else { //Use microseconds since page-load if supported
                        rd = (dt2 + rd) % 16 | 0;
                        dt2 = Math.floor(dt2 / 16);
                    }
                    return (c === 'x' ? rd : (rd & 0x3 | 0x8)).toString(16);
                });
            };
            
            // Store device hash
            const setDeviceHash = () => {
                const dh = generateDeviceHash();

                if (!lS.hasOwnProperty('device_hash')) {
                    lS.setItem('device_hash', dh);
                }
            };
            
            // Get coordinates and save to local storage
            const coordinates = (geoPosition) => {              
                const lat = geoPosition.coords.latitude;
                const lng = geoPosition.coords.longitude;
                
                const savedLat = lS.getItem('lat') ?? null;
                const savedLng = lS.getItem('lng') ?? null;
                
                if (!lS.hasOwnProperty('lat') || savedLat !== lat) {
                    lS.setItem('lat', lat);
                }
                
                if (!lS.hasOwnProperty('lng') || savedLng !== lng) {
                    lS.setItem('lng', lng);
                }
            };
            
            // Get user IP detailed information
            const getIPDetails = async () => {
                try {
                    const response = await fetch("https://ipapi.co/json/");
                    const data = await response.json();
                    return data;
                } catch (e) {
                    console.error("Error:", e);
                }
            }
            
            // Set user IP to local storage
            const setUserIP = async () => {
                const IPdata = await getIPDetails();
                const publicIP = IPdata['ip'];
                const savedIp = lS.getItem('user_public_ip') ?? '127.0.0.1';
                
                if (!lS.hasOwnProperty('user_public_ip') || savedIp !== publicIP) {
                    lS.setItem('user_public_ip', publicIP);
                    lS.setItem('user_public_data', JSON.stringify(IPdata));
                }
            }
            
            // Run code after DOM ready
            document.addEventListener('DOMContentLoaded', () => {    
                // Set device hash to local storage
                setDeviceHash();
                // Check navigator have to customer coordinates
                if (navigator.geolocation) {
                    // Get coordinates form GeoLocation API
                    navigator.geolocation.getCurrentPosition(coordinates);
                } else {
                    //TODO: Release geolocation by the backend
                    console.log('GeoLocation API not supported');
                }
                // Set external user IP to local storage
                setUserIP();
            });
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
