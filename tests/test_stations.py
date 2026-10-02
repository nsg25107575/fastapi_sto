"""Tests for POST/GET/PUT/DELETE /stations and /stations/nearest."""


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


def test_create_duplicate_station_returns_409(auth_client):
    client, _user = auth_client
    payload = {"name": "Duplicate STO", "address": "2 Main St"}

    first = client.post("/stations/", json=payload)
    assert first.status_code == 201

    second = client.post("/stations/", json=payload)
    assert second.status_code == 409


def test_get_stations_lists_all(auth_client):
    client, _user = auth_client
    client.post("/stations/", json={"name": "STO A", "address": "A St"})
    client.post("/stations/", json={"name": "STO B", "address": "B St"})

    response = client.get("/stations/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_get_stations_empty_list_when_none_exist(client):
    response = client.get("/stations/")

    assert response.status_code == 200
    assert response.json() == []


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
