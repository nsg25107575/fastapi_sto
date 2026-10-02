"""Integration tests for POST /orders and GET /orders/{id} -- the
"find nearest station -> order a service" flow:
  1. POST /customer           -> get a customer_id (anonymous)
  2. GET  /stations/nearest   -> pick a station_id + station_service_id
  3. POST /orders             -> place the order
"""


def _make_customer(client):
    response = client.post(
        "/customer/",
        json={"lat": 50.4501, "lng": 30.5234, "public_data": {}},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _make_station_with_service(auth_client, db_session):
    """Create a station (owned by the authenticated user) with one
    service. The service is added directly via the model layer, since
    there is no "create service" step relevant to this test beyond
    having a valid station_service_id to order."""
    client, _user_payload = auth_client

    station_response = client.post(
        "/stations/", json={"name": "Order Flow STO", "address": "Order Flow St"}
    )
    assert station_response.status_code == 201, station_response.text
    station = station_response.json()

    from models.station import StationModel
    from models.station_service import StationServiceModel

    db_station = StationModel.read_station(db_session, station["id"])
    db_station.latitude = 50.4501
    db_station.longitude = 30.5234
    db_session.commit()

    service = StationServiceModel.add_service(
        session=db_session,
        station_id=station["id"],
        name="Tire change",
        price=100.0,
    )

    return station["id"], service.id


def test_create_order_success(auth_client, db_session, client):
    station_id, service_id = _make_station_with_service(auth_client, db_session)
    customer = _make_customer(client)

    response = client.post(
        "/orders/",
        json={
            "customer_id": customer["id"],
            "station_id": station_id,
            "station_service_id": service_id,
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["station_id"] == station_id
    assert data["station_service_id"] == service_id
    assert data["status"] == "pending"


def test_create_order_rejects_mismatched_station_and_service(auth_client, db_session, client):
    station_id, _service_id = _make_station_with_service(auth_client, db_session)
    customer = _make_customer(client)

    response = client.post(
        "/orders/",
        json={
            "customer_id": customer["id"],
            "station_id": station_id,
            "station_service_id": 999999,
        },
    )

    assert response.status_code == 400


def test_create_order_customer_not_found(client):
    response = client.post(
        "/orders/",
        json={
            "customer_id": 999999,
            "station_id": 1,
            "station_service_id": 1,
        },
    )

    assert response.status_code == 400


def test_get_order_by_id(auth_client, db_session, client):
    station_id, service_id = _make_station_with_service(auth_client, db_session)
    customer = _make_customer(client)

    created = client.post(
        "/orders/",
        json={
            "customer_id": customer["id"],
            "station_id": station_id,
            "station_service_id": service_id,
        },
    ).json()

    response = client.get(f"/orders/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_order_not_found(client):
    response = client.get("/orders/999999")

    assert response.status_code == 404


def test_update_order_status_requires_auth(auth_client, db_session, client):
    station_id, service_id = _make_station_with_service(auth_client, db_session)
    customer = _make_customer(client)

    created = client.post(
        "/orders/",
        json={
            "customer_id": customer["id"],
            "station_id": station_id,
            "station_service_id": service_id,
        },
    ).json()

    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as anon_client:
        response = anon_client.put(
            f"/orders/{created['id']}/status",
            json={"status": "confirmed"},
        )

    assert response.status_code == 401


def test_update_order_status_success(auth_client, db_session):
    client, _user = auth_client
    station_id, service_id = _make_station_with_service(auth_client, db_session)
    customer = _make_customer(client)

    created = client.post(
        "/orders/",
        json={
            "customer_id": customer["id"],
            "station_id": station_id,
            "station_service_id": service_id,
        },
    ).json()

    response = client.put(
        f"/orders/{created['id']}/status",
        json={"status": "confirmed"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


def test_update_order_status_not_found(auth_client):
    client, _user = auth_client

    response = client.put(
        "/orders/999999/status",
        json={"status": "confirmed"},
    )

    assert response.status_code == 404
