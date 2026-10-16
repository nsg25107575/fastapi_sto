"""Integration tests for POST /orders and GET /orders/{id} -- the
"find nearest station -> order a service" flow:
  1. POST /customer           -> get a customer_id (anonymous)
  2. GET  /stations/nearest   -> pick a station_id + station_service_id
  3. POST /orders             -> place the order
"""

from sqlalchemy import select

from config import Config
from i18n.dependency_translator import t
from models.chat_message import ChatMessageModel, MessageType, SenderType
from models.chat_room import ChatRoomModel


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
    station_id, service_id = _make_station_with_service(
        auth_client,
        db_session,
    )
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

    chat_room = db_session.scalar(
        select(ChatRoomModel).where(
            ChatRoomModel.order_id == data["id"]
        )
    )

    assert chat_room is not None
    assert chat_room.order_id == data["id"]


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
    station_id, service_id = _make_station_with_service(
        auth_client,
        db_session,
    )
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

    chat_room = db_session.scalar(
        select(ChatRoomModel).where(
            ChatRoomModel.order_id == created["id"]
        )
    )

    assert chat_room is not None

    message = db_session.scalar(
        select(ChatMessageModel).where(
            ChatMessageModel.chat_room_id == chat_room.id
        )
    )

    assert message is not None
    assert message.message_type == MessageType.SYSTEM
    assert message.sender_type == SenderType.SYSTEM
    assert message.sender_id is None
    expected_messages = {
        t(
            "order.status_updated",
            locale=locale["abbr"],
            status=t("order.confirmed", locale=locale["abbr"]),
        )
        for locale in Config.app_sup_locales
    }
    assert message.body in expected_messages


def test_update_order_status_not_found(auth_client):
    client, _user = auth_client

    response = client.put(
        "/orders/999999/status",
        json={"status": "confirmed"},
    )

    assert response.status_code == 404


def test_update_order_status_forbidden_for_non_owner(
        auth_client,
        second_auth_client,
        db_session,
        client,
):
    owner_client, _ = auth_client

    station_id, service_id = _make_station_with_service(
        auth_client,
        db_session,
    )
    customer = _make_customer(client)

    created_response = client.post(
        "/orders/",
        json={
            "customer_id": customer["id"],
            "station_id": station_id,
            "station_service_id": service_id,
        },
    )
    assert created_response.status_code == 201, created_response.text
    order_id = created_response.json()["id"]

    response = second_auth_client.put(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
    )

    assert response.status_code == 403

    # The order status must remain unchanged.
    order_response = owner_client.get(f"/orders/{order_id}")
    assert order_response.status_code == 200
    assert order_response.json()["status"] == "pending"

    # No system message should have been created by the rejected request.
    chat_room = db_session.scalar(
        select(ChatRoomModel).where(ChatRoomModel.order_id == order_id)
    )
    assert chat_room is not None

    messages = db_session.scalars(
        select(ChatMessageModel).where(
            ChatMessageModel.chat_room_id == chat_room.id
        )
    ).all()

    assert messages == []


def test_update_order_status_accepts_in_progress(
        auth_client, db_session, client
):
    station_id, service_id = _make_station_with_service(
        auth_client, db_session
    )
    customer = _make_customer(client)

    created = client.post(
        "/orders/",
        json={
            "customer_id": customer["id"],
            "station_id": station_id,
            "station_service_id": service_id,
        },
    )
    assert created.status_code == 201, created.text

    response = auth_client[0].put(
        f"/orders/{created.json()['id']}/status",
        json={"status": "in_progress"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "in_progress"


def test_update_order_status_accepts_completed(
        auth_client, db_session, client
):
    station_id, service_id = _make_station_with_service(
        auth_client, db_session
    )
    customer = _make_customer(client)

    created = client.post(
        "/orders/",
        json={
            "customer_id": customer["id"],
            "station_id": station_id,
            "station_service_id": service_id,
        },
    )
    assert created.status_code == 201, created.text

    response = auth_client[0].put(
        f"/orders/{created.json()['id']}/status",
        json={"status": "completed"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "completed"


def test_update_order_status_rejects_invalid_status(auth_client):
    response = auth_client[0].put(
        "/orders/1/status",
        json={"status": "invalid_status"},
    )

    assert response.status_code == 422
