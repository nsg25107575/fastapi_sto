"""Tests for POST/GET/PUT/DELETE /stations and /stations/nearest."""

import pytest

from models.customer import CustomerModel
from models.order import OrderModel, OrderStatus
from models.review import ReviewModel
from models.station import ModerationStatus, StationModel
from models.station_service import StationServiceModel


def test_create_station_requires_auth(client):
    response = client.post(
        "/stations/",
        json={"name": "Test STO", "address": "1 Main St"},
    )

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
    """POST /stations resolves the address and persists coordinates."""
    client, _user = auth_client

    response = client.post(
        "/stations/",
        json={
            "name": "Geocoded STO",
            "address": "1 Khreshchatyk St, Kyiv",
        },
    )
    assert response.status_code == 201, response.text

    station = StationModel.read_station(
        db_session,
        response.json()["id"],
    )

    # Numeric columns round-trip as Decimal, not float.
    assert float(station.latitude) == pytest.approx(50.4501)
    assert float(station.longitude) == pytest.approx(30.5234)


def test_create_station_returns_400_when_geocoding_fails(
        auth_client,
        monkeypatch,
):
    from services.geocoding import GeocodingError

    monkeypatch.setattr(
        "routers.stations.geocode_address",
        lambda address: (_ for _ in ()).throw(
            GeocodingError("no results")
        ),
    )

    client, _user = auth_client

    response = client.post(
        "/stations/",
        json={
            "name": "Unresolvable STO",
            "address": "nowhere in particular",
        },
    )

    assert response.status_code == 400


def test_create_duplicate_station_returns_409(auth_client):
    client, _user = auth_client
    payload = {
        "name": "Duplicate STO",
        "address": "2 Main St",
    }

    first = client.post("/stations/", json=payload)
    assert first.status_code == 201

    second = client.post("/stations/", json=payload)
    assert second.status_code == 409


def test_update_station_address_regeocodes(auth_client, db_session):
    """Changing address must update the station coordinates."""
    client, _user = auth_client

    created_response = client.post(
        "/stations/",
        json={
            "name": "Movable STO",
            "address": "Old Address",
        },
    )
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()

    response = client.put(
        f"/stations/{created['id']}",
        json={"address": "1 Khreshchatyk St, Kyiv"},
    )
    assert response.status_code == 200, response.text

    station = StationModel.read_station(db_session, created["id"])

    assert station.address == "1 Khreshchatyk St, Kyiv"
    assert float(station.latitude) == pytest.approx(50.4501)
    assert float(station.longitude) == pytest.approx(30.5234)


def test_update_station_without_address_change_skips_geocoding(
        auth_client,
        monkeypatch,
):
    """Updating unrelated fields must not trigger geocoding."""
    client, _user = auth_client

    created_response = client.post(
        "/stations/",
        json={
            "name": "Stable STO",
            "address": "Stable St",
        },
    )
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()

    def fail_if_called(address):
        raise AssertionError(
            "geocode_address should not be called when address is unchanged"
        )

    monkeypatch.setattr(
        "routers.stations.geocode_address",
        fail_if_called,
    )

    response = client.put(
        f"/stations/{created['id']}",
        json={"active": False},
    )

    assert response.status_code == 200, response.text


def test_get_stations_lists_all(auth_client):
    """GET /stations returns a paginated list and total count."""
    client, _user = auth_client

    client.post(
        "/stations/",
        json={"name": "STO A", "address": "A St"},
    )
    client.post(
        "/stations/",
        json={"name": "STO B", "address": "B St"},
    )

    response = client.get("/stations/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["limit"] == 20
    assert data["offset"] == 0


def test_get_stations_empty_list_when_none_exist(client):
    """GET /stations returns an empty list when no stations exist."""
    response = client.get("/stations/")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_get_stations_respects_limit(auth_client):
    """GET /stations supports pagination with limit."""
    client, _user = auth_client

    for letter in "ABC":
        client.post(
            "/stations/",
            json={
                "name": f"STO {letter}",
                "address": f"{letter} St",
            },
        )

    response = client.get(
        "/stations/",
        params={"limit": 2},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0


def test_get_stations_respects_offset(auth_client):
    """GET /stations supports pagination with offset."""
    client, _user = auth_client

    for letter in "ABC":
        client.post(
            "/stations/",
            json={
                "name": f"STO {letter}",
                "address": f"{letter} St",
            },
        )

    first_page = client.get(
        "/stations/",
        params={"limit": 2, "offset": 0},
    ).json()

    second_page = client.get(
        "/stations/",
        params={"limit": 2, "offset": 2},
    ).json()

    assert len(first_page["items"]) == 2
    assert len(second_page["items"]) == 1

    first_ids = {item["id"] for item in first_page["items"]}
    second_ids = {item["id"] for item in second_page["items"]}

    assert first_ids.isdisjoint(second_ids)


def test_get_stations_offset_beyond_total_returns_empty_items(auth_client):
    """An offset beyond total returns no items but preserves total."""
    client, _user = auth_client

    client.post(
        "/stations/",
        json={"name": "STO A", "address": "A St"},
    )

    response = client.get(
        "/stations/",
        params={"offset": 100},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 1


def test_get_stations_rejects_limit_above_max(auth_client):
    """GET /stations rejects a limit above 100."""
    client, _user = auth_client

    response = client.get(
        "/stations/",
        params={"limit": 101},
    )

    assert response.status_code == 422


def test_get_stations_rejects_negative_offset(auth_client):
    """GET /stations rejects a negative offset."""
    client, _user = auth_client

    response = client.get(
        "/stations/",
        params={"offset": -1},
    )

    assert response.status_code == 422


def test_get_station_by_id(auth_client):
    client, _user = auth_client

    created = client.post(
        "/stations/",
        json={"name": "STO C", "address": "C St"},
    ).json()

    response = client.get(f"/stations/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "STO C"


def test_get_station_not_found(client):
    response = client.get("/stations/999999")

    assert response.status_code == 404


def test_update_station_requires_auth(auth_client):
    client, _user = auth_client

    created = client.post(
        "/stations/",
        json={"name": "STO D", "address": "D St"},
    )
    assert created.status_code == 201, created.text
    station_id = created.json()["id"]

    from fastapi.testclient import TestClient
    from main import app

    # Unauthenticated client sharing the same app and dependency overrides.
    with TestClient(app) as anon_client:
        response = anon_client.put(
            f"/stations/{station_id}",
            json={"name": "Hacked"},
        )

    assert response.status_code == 401


def test_update_station_success(auth_client):
    client, _user = auth_client

    created = client.post(
        "/stations/",
        json={"name": "STO E", "address": "E St"},
    ).json()

    response = client.put(
        f"/stations/{created['id']}",
        json={
            "name": "Updated Name",
            "address": "Updated Address",
        },
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

    created = client.post(
        "/stations/",
        json={"name": "STO F", "address": "F St"},
    ).json()

    response = client.delete(f"/stations/{created['id']}")
    assert response.status_code == 204

    # Soft-deleted station should no longer be retrievable.
    follow_up = client.get(f"/stations/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_station_not_found(auth_client):
    client, _user = auth_client

    response = client.delete("/stations/999999")

    assert response.status_code == 404


def test_get_nearest_stations_filters_by_coordinates(
        auth_client,
        db_session,
):
    client, user_payload = auth_client

    near = StationModel.create_station(
        session=db_session,
        user_id=user_payload["id"],
        name="Near STO",
        address="Near St",
    )
    near.latitude = 50.4501
    near.longitude = 30.5234
    near.moderation_status = ModerationStatus.APPROVED

    far = StationModel.create_station(
        session=db_session,
        user_id=user_payload["id"],
        name="Far STO",
        address="Far St",
    )
    far.latitude = -33.8688
    far.longitude = 151.2093
    far.moderation_status = ModerationStatus.APPROVED

    db_session.commit()

    response = client.request(
        "GET",
        "/stations/nearest",
        json={"lat": 50.4501, "lng": 30.5234},
    )

    assert response.status_code == 200
    names = [station["name"] for station in response.json()]
    assert "Near STO" in names


def test_get_nearest_stations_rejects_invalid_coordinates(client):
    response = client.request(
        "GET",
        "/stations/nearest",
        json={"lat": 999, "lng": 30.5234},
    )

    assert response.status_code == 400


def test_get_nearest_stations_returns_aggregated_rating(
        auth_client,
        db_session,
):
    client, user_payload = auth_client

    station = StationModel.create_station(
        session=db_session,
        user_id=user_payload["id"],
        name="Rated STO",
        address="Rated St",
    )
    station.latitude = 50.4501
    station.longitude = 30.5234
    db_session.commit()

    service = StationServiceModel.add_service(
        session=db_session,
        station_id=station.id,
        name="Oil change",
        price=250.0,
    )
    db_session.commit()

    station.moderation_status = ModerationStatus.APPROVED
    db_session.commit()

    customer_1 = CustomerModel(
        ip="127.0.0.1",
        device_hash="a" * 36,
        lat=50.4501,
        lng=30.5234,
        public_data={},
    )
    customer_2 = CustomerModel(
        ip="127.0.0.2",
        device_hash="b" * 36,
        lat=50.4501,
        lng=30.5234,
        public_data={},
    )

    db_session.add_all([customer_1, customer_2])
    db_session.commit()

    order_1 = OrderModel.create_order(
        session=db_session,
        customer_id=customer_1.id,
        station_id=station.id,
        station_service_id=service.id,
    )
    db_session.commit()

    OrderModel.update_order_status(
        session=db_session,
        order_id=order_1.id,
        status=OrderStatus.COMPLETED,
    )
    db_session.commit()

    order_2 = OrderModel.create_order(
        session=db_session,
        customer_id=customer_2.id,
        station_id=station.id,
        station_service_id=service.id,
    )
    db_session.commit()

    OrderModel.update_order_status(
        session=db_session,
        order_id=order_2.id,
        status=OrderStatus.COMPLETED,
    )
    db_session.commit()

    ReviewModel.create_review(
        session=db_session,
        order_id=order_1.id,
        station_id=station.id,
        customer_id=customer_1.id,
        rating=5,
    )
    ReviewModel.create_review(
        session=db_session,
        order_id=order_2.id,
        station_id=station.id,
        customer_id=customer_2.id,
        rating=3,
    )
    db_session.commit()

    response = client.request(
        "GET",
        "/stations/nearest",
        json={
            "lat": 50.4501,
            "lng": 30.5234,
        },
    )

    assert response.status_code == 200

    rated_station = next(
        item
        for item in response.json()
        if item["id"] == station.id
    )

    assert rated_station["rating"] == 4.0
    assert rated_station["reviews_count"] == 2


def test_update_station_forbidden_for_non_owner(
        auth_client,
        second_auth_client,
):
    owner_client, _owner = auth_client
    second_client, _second_user = second_auth_client

    created = owner_client.post(
        "/stations/",
        json={
            "name": "Protected STO",
            "address": "Protected Street",
        },
    )
    assert created.status_code == 201, created.text
    station_id = created.json()["id"]

    response = second_client.put(
        f"/stations/{station_id}",
        json={"name": "Hacked STO"},
    )

    assert response.status_code == 403

    # The original owner can still see the unchanged station.
    station = owner_client.get(f"/stations/{station_id}")
    assert station.status_code == 200
    assert station.json()["name"] == "Protected STO"


def test_delete_station_forbidden_for_non_owner(
        auth_client,
        second_auth_client,
):
    owner_client, _owner = auth_client
    second_client, _second_user = second_auth_client

    created = owner_client.post(
        "/stations/",
        json={
            "name": "Protected Delete STO",
            "address": "Protected Street",
        },
    )
    assert created.status_code == 201, created.text
    station_id = created.json()["id"]

    response = second_client.delete(f"/stations/{station_id}")

    assert response.status_code == 403

    # The station must not have been soft-deleted.
    station = owner_client.get(f"/stations/{station_id}")
    assert station.status_code == 200
    assert station.json()["name"] == "Protected Delete STO"


def _assign_station_role(
        db_session,
        station_id,
        user_id,
        role_name,
):
    """Create a station role and assign it to a user."""
    from models.station_role import StationRoleModel
    from models.station_user import StationUserModel

    role = StationRoleModel(
        name=role_name,
        description=f"{role_name} role for testing",
    )
    db_session.add(role)
    db_session.flush()

    assignment = StationUserModel(
        station_id=station_id,
        user_id=user_id,
        role_id=role.id,
    )
    db_session.add(assignment)
    db_session.commit()

    return assignment


def test_station_owner_can_update_station(auth_client):
    """The station owner can still update their own station."""
    client, _user = auth_client

    created = client.post(
        "/stations/",
        json={
            "name": "Owner STO",
            "address": "Owner Street",
        },
    )
    assert created.status_code == 201, created.text

    response = client.put(
        f"/stations/{created.json()['id']}",
        json={"name": "Updated Owner STO"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Updated Owner STO"


def test_manager_can_update_assigned_station(
        auth_client,
        second_auth_client,
        db_session,
):
    """A Manager assigned to a station can update it."""
    owner_client, _owner = auth_client
    manager_client, manager_user_payload = second_auth_client

    created = owner_client.post(
        "/stations/",
        json={
            "name": "Manager STO",
            "address": "Manager Street",
        },
    )
    assert created.status_code == 201, created.text
    station_id = created.json()["id"]

    _assign_station_role(
        db_session,
        station_id=station_id,
        user_id=manager_user_payload["id"],
        role_name="Manager",
    )

    response = manager_client.put(
        f"/stations/{station_id}",
        json={"name": "Updated Manager STO"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Updated Manager STO"


def test_cashier_cannot_update_assigned_station(
        auth_client,
        second_auth_client,
        db_session,
):
    """A Cashier cannot update station settings."""
    owner_client, _owner = auth_client
    cashier_client, cashier_user_payload = second_auth_client

    created = owner_client.post(
        "/stations/",
        json={
            "name": "Cashier STO",
            "address": "Cashier Street",
        },
    )
    assert created.status_code == 201, created.text
    station_id = created.json()["id"]

    _assign_station_role(
        db_session,
        station_id=station_id,
        user_id=cashier_user_payload["id"],
        role_name="Cashier",
    )

    response = cashier_client.put(
        f"/stations/{station_id}",
        json={"name": "Unauthorized Update"},
    )

    assert response.status_code == 403


def test_manager_cannot_delete_assigned_station(
        auth_client,
        second_auth_client,
        db_session,
):
    """A Manager may update a station but cannot delete it."""
    owner_client, _owner = auth_client
    manager_client, manager_user_payload = second_auth_client

    created = owner_client.post(
        "/stations/",
        json={
            "name": "Protected STO",
            "address": "Protected Street",
        },
    )
    assert created.status_code == 201, created.text
    station_id = created.json()["id"]

    _assign_station_role(
        db_session,
        station_id=station_id,
        user_id=manager_user_payload["id"],
        role_name="Manager",
    )

    response = manager_client.delete(f"/stations/{station_id}")

    assert response.status_code == 403

    # The station must remain available after the forbidden request.
    station_response = owner_client.get(f"/stations/{station_id}")
    assert station_response.status_code == 200
    assert station_response.json()["name"] == "Protected STO"
