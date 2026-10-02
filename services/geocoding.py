"""Address -> (lat, lng) geocoding, used when creating a station so its
coordinates (needed by GET /stations/nearest) don't have to be entered
manually.

Default provider is OpenStreetMap's free Nominatim API -- no API key
required, but its usage policy requires a descriptive User-Agent header
(set via Config.geocoding_user_agent) and reasonable request volume.
Provider/timeout are configurable via GEOCODING_* env vars (see
config/config.py) so a paid provider can be swapped in later without
touching this module's call sites.
"""
import httpx

from config import Config


class GeocodingError(Exception):
    """Raised when an address cannot be resolved to coordinates -- no
    results, a non-2xx response from the provider, or a network error.
    Callers (routers) are expected to catch this and map it to a client-
    facing error rather than letting a raw httpx exception leak out."""


def geocode_address(address: str) -> tuple[float, float]:
    """
    Resolve a free-text address to (latitude, longitude).

    Raises:
        ValueError: `address` is empty/blank -- a caller bug, not a
            geocoding failure, so it's distinguished from GeocodingError.
        GeocodingError: the provider returned no results, a non-2xx
            response, or the request failed (network/timeout).
    """
    if not address or not address.strip():
        raise ValueError("address must not be empty")

    try:
        response = httpx.get(
            Config.geocoding_base_url,
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": Config.geocoding_user_agent},
            timeout=Config.geocoding_timeout,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise GeocodingError(f"Geocoding provider request failed: {exc}") from exc

    results = response.json()
    if not results:
        raise GeocodingError(f"No coordinates found for address: {address!r}")

    first = results[0]
    return float(first["lat"]), float(first["lon"])
