"""Tests for POST/GET/PUT/DELETE /stations and /stations/nearest."""

import pytest


def test_create_station_requires_auth(client):
    response = client.post("/stations/", json={"name": "Test STO", "address": "1 Main St"})

    assert response.status_code == 401


def test_create_station_success(auth_client):
    client, _user = auth_client

    response = client.post(
        "/stations/",
        json={"name": "Test STO", "address": "1 Main St"},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "Test STO"
    assert data["address"] == "1 Main St"
    assert "id" in data


def test_create_station_geocodes_address(auth_client, db_session):
    """POST /stations resolves the address to coordinates via the
    geocoding service (stubbed in conftest.py's autouse fixture) and
    persists them -- without this, the station would be invisible to
    GET /stations/nearest (which requires non-null lat/lng)."""
    client, _user = auth_client

    response = client.post(
        "/stations/",
        json={"name": "Geocoded STO", "address": "1 Khreshchatyk St, Kyiv"},
    )
    assert response.status_code == 201, response.text

    from models.station import StationModel

    station = StationModel.read_station(db_session, response.json()["id"])
    # Numeric(16,14) columns round-trip as decimal.Decimal, not float --
    # pytest.approx can't subtract float from Decimal directly.
    assert float(station.latitude) == pytest.approx(50.4501)
    assert float(station.longitude) == pytest.approx(30.5234)


def test_create_station_returns_400_when_geocoding_fails(auth_client, monkeypatch):
    from services.geocoding import GeocodingError

    monkeypatch.setattr(
        "routers.stations.geocode_address",
        lambda address: (_ for _ in ()).throw(GeocodingError("no results")),
    )
    client, _user = auth_client

    response = client.post(
        "/stations/",
        json={"name": "Unresolvable STO", "address": "nowhere in particular"},
    )

    assert response.status_code == 400


def test_create_duplicate_station_returns_409(auth_client):
    client, _user = auth_client
    payload = {"name": "Duplicate STO", "address": "2 Main St"}

    first = client.post("/stations/", json=payload)
    assert first.status_code == 201

    second = client.post("/stations/", json=payload)
    assert second.status_code == 409


def test_update_station_address_regeocodes(auth_client, db_session):
    """PUT /stations/{id} re-resolves coordinates when `address`
    changes -- otherwise lat/lng would silently keep pointing at the
    OLD address."""
    client, _user = auth_client
    created = client.post(
        "/stations/", json={"name": "Movable STO", "address": "Old Address"}
    ).json()

    response = client.put(
        f"/stations/{created['id']}",
        json={"address": "1 Khreshchatyk St, Kyiv"},
    )
    assert response.status_code == 200, response.text

    from models.station import StationModel

    station = StationModel.read_station(db_session, created["id"])
    assert station.address == "1 Khreshchatyk St, Kyiv"
    assert float(station.latitude) == pytest.approx(50.4501)
    assert float(station.longitude) == pytest.approx(30.5234)


def test_update_station_without_address_change_skips_geocoding(auth_client, monkeypatch):
    """Updating unrelated fields (e.g. `active`) must NOT trigger a
    geocoding call at all."""
    client, _user = auth_client
    created = client.post(
        "/stations/", json={"name": "Stable STO", "address": "Stable St"}
    ).json()

    def _fail_if_called(address):
        raise AssertionError("geocode_address should not be called when address is unchanged")

    monkeypatch.setattr("routers.stations.geocode_address", _fail_if_called)

    response = client.put(f"/stations/{created['id']}", json={"active": False})

    assert response.status_code == 200, response.text


def test_get_stations_lists_all(auth_client):
    """
    GET /stations returns a paginated list of all stations, with total count and pagination metadata.
    The default limit is 20, and offset is 0.
    """
    client, _user = auth_client
    client.post("/stations/", json={"name": "STO A", "address": "A St"})
    client.post("/stations/", json={"name": "STO B", "address": "B St"})

    response = client.get("/stations/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["limit"] == 20
    assert data["offset"] == 0


def test_get_stations_empty_list_when_none_exist(client):
    """
    GET /stations returns an empty list and total count of 0 when no stations exist.
    """
    response = client.get("/stations/")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_get_stations_respects_limit(auth_client):
    """
    GET /stations supports limit and offset query parameters for pagination.
    """
    client, _user = auth_client
    for letter in "ABC":
        client.post("/stations/", json={"name": f"STO {letter}", "address": f"{letter} St"})

    response = client.get("/stations/", params={"limit": 2})

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3  # total reflects ALL rows, not just this page
    assert data["limit"] == 2
    assert data["offset"] == 0


def test_get_stations_respects_offset(auth_client):
    """
    GET /stations supports offset query parameter for pagination,
    allowing clients to retrieve subsequent pages of results.
    """
    client, _user = auth_client
    for letter in "ABC":
        client.post("/stations/", json={"name": f"STO {letter}", "address": f"{letter} St"})

    first_page = client.get("/stations/", params={"limit": 2, "offset": 0}).json()
    second_page = client.get("/stations/", params={"limit": 2, "offset": 2}).json()

    assert len(first_page["items"]) == 2
    assert len(second_page["items"]) == 1  # only 1 left (3 total, offset 2)
    first_ids = {item["id"] for item in first_page["items"]}
    second_ids = {item["id"] for item in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)  # no overlap between pages


def test_get_stations_offset_beyond_total_returns_empty_items(auth_client):
    """
    GET /stations with an offset greater than the total number of stations returns an empty list of items,
    but the total count remains accurate.
    """
    client, _user = auth_client
    client.post("/stations/", json={"name": "STO A", "address": "A St"})

    response = client.get("/stations/", params={"offset": 100})

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 1  # total count is unaffected by offset


def test_get_stations_rejects_limit_above_max(auth_client):
    """
    GET /stations with a limit greater than the maximum allowed (100) returns a 422 Unprocessable Entity error.
    """
    client, _user = auth_client

    response = client.get("/stations/", params={"limit": 101})

    assert response.status_code == 422


def test_get_stations_rejects_negative_offset(auth_client):
    """
    GET /stations with a negative offset returns a 422 Unprocessable Entity error.
    """
    client, _user = auth_client

    response = client.get("/stations/", params={"offset": -1})

    assert response.status_code == 422


def test_get_station_by_id(auth_client):
    client, _user = auth_client
    created = client.post("/stations/", json={"name": "STO C", "address": "C St"}).json()

    response = client.get(f"/stations/{created["id"]}")

    assert response.status_code == 200
    assert response.json()["name"] == "STO C"


def test_get_station_not_found(client):
    response = client.get("/stations/999999")

    assert response.status_code == 404


def test_update_station_requires_auth(auth_client):
    client, _user = auth_client
    created = client.post("/stations/", json={"name": "STO D", "address": "D St"}).json()

    # Build an unauthenticated client sharing the same app/overrides.
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as anon_client:
        response = anon_client.put(
            f"/stations/{created["id"]}",
            json={"name": "Hacked"},
        )

    assert response.status_code == 401


def test_update_station_success(auth_client):
    client, _user = auth_client
    created = client.post("/stations/", json={"name": "STO E", "address": "E St"}).json()

    response = client.put(
        f"/stations/{created["id"]}",
        json={"name": "Updated Name", "address": "Updated Address"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["address"] == "Updated Address"


def test_update_station_not_found(auth_client):
    client, _user = auth_client

    response = client.put(
        "/stations/999999",
        json={"name": "Does not matter"},
    )

    assert response.status_code == 404


def test_delete_station_success(auth_client):
    client, _user = auth_client
    created = client.post("/stations/", json={"name": "STO F", "address": "F St"}).json()

    response = client.delete(f"/stations/{created["id"]}")
    assert response.status_code == 204

    # Soft-deleted station should no longer be retrievable.
    follow_up = client.get(f"/stations/{created["id"]}")
    assert follow_up.status_code == 404


def test_delete_station_not_found(auth_client):
    client, _user = auth_client

    response = client.delete("/stations/999999")

    assert response.status_code == 404


def test_get_nearest_stations_filters_by_coordinates(auth_client, db_session):
    client, user_payload = auth_client

    from models.station import StationModel

    near = StationModel.create_station(
        session=db_session,
        user_id=user_payload["id"],
        name="Near STO",
        address="Near St",
    )
    near.latitude = 50.4501
    near.longitude = 30.5234

    far = StationModel.create_station(
        session=db_session,
        user_id=user_payload["id"],
        name="Far STO",
        address="Far St",
    )
    far.latitude = -33.8688
    far.longitude = 151.2093
    db_session.commit()

    response = client.request(
        "GET",
        "/stations/nearest",
        json={"lat": 50.4501, "lng": 30.5234},
    )

    assert response.status_code == 200
    names = [s["name"] for s in response.json()]
    assert "Near STO" in names


def test_get_nearest_stations_rejects_invalid_coordinates(client):
    response = client.request(
        "GET",
        "/stations/nearest",
        json={"lat": 999, "lng": 30.5234},
    )

    assert response.status_code == 400
