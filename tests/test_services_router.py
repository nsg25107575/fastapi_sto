"""Tests for /services/* (per-station price list)."""


def _create_station(auth_client):
    client, user_payload = auth_client
    response = client.post(
        "/stations/",
        json={"name": "Service STO", "address": "Service St"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_service_requires_auth(client):
    response = client.post(
        "/services/",
        params={"station_id": 1, "name": "Oil change", "price": 20.0},
    )

    assert response.status_code == 401


def test_create_service_success(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    response = client.post(
        "/services/",
        params={"station_id": station_id, "name": "Oil change", "price": 20.0},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Oil change"
    assert data["price"] == 20.0


def test_read_services_aggregates_min_max_price(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    client.post(
        "/services/",
        params={"station_id": station_id, "name": "Tire change", "price": 10.0},
    )
    client.post(
        "/services/",
        params={"station_id": station_id, "name": "Tire change", "price": 15.0},
    )

    response = client.get("/services/")

    assert response.status_code == 200
    rows = response.json()
    tire_row = next(r for r in rows if r["name"] == "Tire change")
    assert tire_row["min_price"] == 10.0
    assert tire_row["max_price"] == 15.0


def test_read_service_by_id(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    created = client.post(
        "/services/",
        params={"station_id": station_id, "name": "Brake check", "price": 30.0},
    ).json()

    response = client.get(f"/services/{created["id"]}")

    assert response.status_code == 200
    assert response.json()["name"] == "Brake check"


def test_read_service_not_found(client):
    response = client.get("/services/999999")

    assert response.status_code == 404


def test_edit_service_requires_auth(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)
    created = client.post(
        "/services/",
        params={"station_id": station_id, "name": "Battery check", "price": 5.0},
    ).json()

    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as anon_client:
        response = anon_client.put(
            f"/services/{created["id"]}",
            params={"price": 999.0},
        )

    assert response.status_code == 401


def test_edit_service_success(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)
    created = client.post(
        "/services/",
        params={"station_id": station_id, "name": "Battery check", "price": 5.0},
    ).json()

    response = client.put(
        f"/services/{created["id"]}",
        params={"price": 7.5},
    )

    assert response.status_code == 200
    assert response.json()["price"] == 7.5


def test_edit_service_not_found(auth_client):
    client, _user = auth_client

    response = client.put(
        "/services/999999",
        params={"price": 1.0},
    )

    assert response.status_code == 404


def test_remove_service_success(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)
    created = client.post(
        "/services/",
        params={"station_id": station_id, "name": "Wash", "price": 3.0},
    ).json()

    response = client.delete(f"/services/{created["id"]}")

    assert response.status_code == 200
    assert response.json() == created["id"]

    follow_up = client.get(f"/services/{created["id"]}")
    assert follow_up.status_code == 404


def test_remove_service_not_found(auth_client):
    client, _user = auth_client

    response = client.delete("/services/999999")

    assert response.status_code == 404
