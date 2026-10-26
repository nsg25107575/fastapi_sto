"""Tests for /services/* (per-station price list)."""

from models.station import StationModel


def _create_station(auth_client):
    client, user_payload = auth_client
    response = client.post(
        "/stations/",
        json={"name": "Service STO", "address": "Service St"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _set_station_moderation_status(db_session, station_id: int, status: str):
    station = db_session.get(StationModel, station_id)
    assert station is not None

    station.moderation_status = status
    db_session.commit()


def test_create_service_requires_auth(client):
    response = client.post(
        "/services/",
        json={"station_id": 1, "name": "Oil change", "price": 20.0},
    )

    assert response.status_code == 401


def test_create_service_success(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    response = client.post(
        "/services/",
        json={"station_id": station_id, "name": "Oil change", "price": 20.0},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "Oil change"
    assert data["price"] == 20.0


def test_create_service_fails_for_nonexistent_station(auth_client):
    client, _ = auth_client

    response = client.post(
        "/services/",
        json={
            "station_id": 999999,
            "name": "Oil change",
            "price": 20.0,
        },
    )

    assert response.status_code == 404


def test_read_service_by_id(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    created = client.post(
        "/services/",
        json={"station_id": station_id, "name": "Brake check", "price": 30.0},
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
        json={"station_id": station_id, "name": "Battery check", "price": 5.0},
    ).json()

    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as anon_client:
        response = anon_client.put(
            f"/services/{created["id"]}",
            json={"price": 999.0},
        )

    assert response.status_code == 401


def test_edit_service_success(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)
    created = client.post(
        "/services/",
        json={"station_id": station_id, "name": "Battery check", "price": 5.0},
    ).json()

    response = client.put(
        f"/services/{created["id"]}",
        json={"price": 7.5},
    )

    assert response.status_code == 200
    assert response.json()["price"] == 7.5


def test_edit_service_not_found(auth_client):
    client, _user = auth_client

    response = client.put(
        "/services/999999",
        json={"price": 1.0},
    )

    assert response.status_code == 404


def test_remove_service_success(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)
    created = client.post(
        "/services/",
        json={"station_id": station_id, "name": "Wash", "price": 3.0},
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


def test_read_services_returns_distinct_names(auth_client):
    """
    Test that the /services/ endpoint returns distinct service names,
    even if multiple price rows exist for the same service.
    """
    client, _user = auth_client
    station_id = _create_station(auth_client)

    client.post("/services/", json={"station_id": station_id, "name": "Tire change", "price": 10.0})
    client.post("/services/", json={"station_id": station_id, "name": "Tire change", "price": 15.0})
    client.post("/services/", json={"station_id": station_id, "name": "Oil change", "price": 20.0})

    response = client.get("/services/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2  # "Tire change" counted once despite two price rows
    assert sorted(data["items"]) == ["Oil change", "Tire change"]


def test_read_services_respects_limit(auth_client):
    """
    Test that the /services/ endpoint respects the 'limit' query parameter
    and returns the correct number of items, while still providing the total count of distinct services.
    """
    client, _user = auth_client
    station_id = _create_station(auth_client)

    for name in ("Oil", "Tire", "Brake"):
        client.post("/services/", json={"station_id": station_id, "name": name, "price": 10.0})

    response = client.get("/services/", params={"limit": 2})

    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3


def test_read_services_rejects_limit_above_max(auth_client):
    """
    Test that the /services/ endpoint rejects requests with a 'limit' parameter above the maximum allowed value (100).
    """
    client, _user = auth_client
    response = client.get("/services/", params={"limit": 101})

    assert response.status_code == 422


def test_read_service_returns_translated_not_found_message_for_uk(auth_client):
    """
    Test that the /services/{service_id} endpoint returns a translated "not found" message
    when the Accept-Language header is set to 'uk'.
    """
    client, _user = auth_client
    response = client.get("/services/999999", headers={"accept-language": "uk"})
    assert response.status_code == 404
    assert response.json()["message"] != "Service not found"  # must be a translation, not an en-fallback


def test_read_service_returns_english_not_found_message_by_default(auth_client):
    """
    Test that the /services/{service_id} endpoint returns an English "not found" message
    when the Accept-Language header is not set or is set to an unsupported language.
    """
    client, _user = auth_client
    response = client.get("/services/999999")
    assert response.status_code == 404
    assert response.json()["message"] == "Service not found"


def test_edit_service_returns_translated_not_found_message(auth_client):
    """
    Test that the /services/{service_id} endpoint returns a translated "not found" message
    when trying to edit a non-existent service with the Accept-Language header set to 'uk'.
    """
    client, _user = auth_client
    response = client.put("/services/999999", json={"name": "x"}, headers={"accept-language": "uk"})
    assert response.status_code == 404
    assert response.json()["message"] != "Service not found"


def test_remove_service_returns_translated_not_found_message(auth_client):
    """
    Test that the /services/{service_id} endpoint returns a translated "not found" message
    when trying to delete a non-existent service with the Accept-Language header set to 'uk'.
    """
    client, _user = auth_client
    response = client.delete("/services/999999", headers={"accept-language": "uk"})
    assert response.status_code == 404
    assert response.json()["message"] != "Service not found"


def test_create_service_resets_station_moderation_to_pending(
        auth_client, db_session
):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    _set_station_moderation_status(db_session, station_id, "approved")

    response = client.post(
        "/services/",
        json={
            "station_id": station_id,
            "name": "Oil change",
            "price": 20.0,
        },
    )

    assert response.status_code == 201, response.text

    db_session.expire_all()
    station = db_session.get(StationModel, station_id)

    assert station.moderation_status == "pending"


def test_edit_service_resets_station_moderation_to_pending(
        auth_client, db_session
):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    created = client.post(
        "/services/",
        json={
            "station_id": station_id,
            "name": "Brake check",
            "price": 30.0,
        },
    )
    assert created.status_code == 201, created.text
    service_id = created.json()["id"]

    _set_station_moderation_status(db_session, station_id, "approved")

    response = client.put(
        f"/services/{service_id}",
        json={"price": 35.0},
    )

    assert response.status_code == 200, response.text

    db_session.expire_all()
    station = db_session.get(StationModel, station_id)

    assert station.moderation_status == "pending"


def test_delete_service_resets_station_moderation_to_pending(
        auth_client, db_session
):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    created = client.post(
        "/services/",
        json={
            "station_id": station_id,
            "name": "Car wash",
            "price": 15.0,
        },
    )
    assert created.status_code == 201, created.text
    service_id = created.json()["id"]

    _set_station_moderation_status(db_session, station_id, "approved")

    response = client.delete(f"/services/{service_id}")

    assert response.status_code == 200, response.text

    db_session.expire_all()
    station = db_session.get(StationModel, station_id)

    assert station.moderation_status == "pending"


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


def test_manager_can_manage_station_services(
        auth_client,
        second_auth_client,
        db_session,
):
    """An assigned Manager can create, update and delete station services."""
    owner_client, _owner = auth_client
    manager_client, manager_user = second_auth_client

    station_id = _create_station(auth_client)

    _assign_station_role(
        db_session,
        station_id=station_id,
        user_id=manager_user["id"],
        role_name="Manager",
    )

    # Manager can create a service.
    created = manager_client.post(
        "/services/",
        json={
            "station_id": station_id,
            "name": "Oil change",
            "price": 20.0,
        },
    )
    assert created.status_code == 201, created.text
    service_id = created.json()["id"]

    # Manager can update the service.
    updated = manager_client.put(
        f"/services/{service_id}",
        json={"price": 25.0},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["price"] == 25.0

    # Manager can delete the service.
    deleted = manager_client.delete(f"/services/{service_id}")
    assert deleted.status_code == 200, deleted.text

    # The service should no longer exist.
    missing = owner_client.get(f"/services/{service_id}")
    assert missing.status_code == 404, missing.text


def test_cashier_cannot_manage_station_services(
        auth_client,
        second_auth_client,
        db_session,
):
    """An assigned Cashier cannot create, update or delete station services."""
    owner_client, _owner = auth_client
    cashier_client, cashier_user = second_auth_client

    station_id = _create_station(auth_client)

    # Create a service as the station owner.
    created = owner_client.post(
        "/services/",
        json={
            "station_id": station_id,
            "name": "Oil change",
            "price": 20.0,
        },
    )
    assert created.status_code == 201, created.text
    service_id = created.json()["id"]

    _assign_station_role(
        db_session,
        station_id=station_id,
        user_id=cashier_user["id"],
        role_name="Cashier",
    )

    # Cashier cannot create a service.
    create_attempt = cashier_client.post(
        "/services/",
        json={
            "station_id": station_id,
            "name": "Car wash",
            "price": 15.0,
        },
    )
    assert create_attempt.status_code == 403, create_attempt.text

    # Cashier cannot update an existing service.
    update_attempt = cashier_client.put(
        f"/services/{service_id}",
        json={"price": 99.0},
    )
    assert update_attempt.status_code == 403, update_attempt.text

    # Cashier cannot delete an existing service.
    delete_attempt = cashier_client.delete(
        f"/services/{service_id}",
    )
    assert delete_attempt.status_code == 403, delete_attempt.text

    # The original service must remain unchanged.
    unchanged = owner_client.get(f"/services/{service_id}")
    assert unchanged.status_code == 200, unchanged.text
    assert unchanged.json()["name"] == "Oil change"
    assert unchanged.json()["price"] == 20.0


def test_create_service_requires_station_id_in_body(auth_client):
    client, _user = auth_client

    response = client.post(
        "/services/",
        json={"name": "Oil change", "price": 20.0},
    )

    assert response.status_code == 422


def test_create_service_requires_name_in_body(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    response = client.post(
        "/services/",
        json={"station_id": station_id, "price": 20.0},
    )

    assert response.status_code == 422


def test_edit_service_accepts_partial_json_body(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    created = client.post(
        "/services/",
        json={
            "station_id": station_id,
            "name": "Oil change",
            "price": 20.0,
        },
    )

    assert created.status_code == 201, created.text

    service_id = created.json()["id"]

    response = client.put(
        f"/services/{service_id}",
        json={"price": 25.0},
    )

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Oil change"
    assert response.json()["price"] == 25.0
