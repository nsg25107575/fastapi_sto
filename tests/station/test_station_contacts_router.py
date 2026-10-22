"""Integration tests for /station-contacts/ CRUD endpoints."""


def _create_station(auth_client, name="Contact STO"):
    if isinstance(auth_client, tuple):
        client, _user = auth_client
    else:
        client = auth_client

    response = client.post(
        "/stations/",
        json={"name": name, "address": f"{name} Address"},
    )

    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_contact(auth_client, station_id, value="+380501234567"):
    if isinstance(auth_client, tuple):
        client, _user = auth_client
    else:
        client = auth_client

    response = client.post(
        "/station-contacts/",
        json={
            "station_id": station_id,
            "type": "phone",
            "value": value,
        },
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_create_station_contact_requires_auth(client):
    response = client.post(
        "/station-contacts/",
        json={
            "station_id": 1,
            "type": "phone",
            "value": "+380501234567",
        },
    )

    assert response.status_code == 401


def test_create_station_contact_success(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    response = client.post(
        "/station-contacts/",
        json={
            "station_id": station_id,
            "type": "phone",
            "value": "+380501234567",
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()
    assert data["station_id"] == station_id
    assert data["type"] == "phone"
    assert data["value"] == "+380501234567"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_station_contact_station_not_found(auth_client):
    client, _user = auth_client

    response = client.post(
        "/station-contacts/",
        json={
            "station_id": 999999,
            "type": "phone",
            "value": "+380501234567",
        },
    )

    assert response.status_code == 404


def test_create_station_contact_forbidden_for_foreign_station(
        auth_client, second_auth_client
):
    client, _user = auth_client
    foreign_station_id = _create_station(
        second_auth_client,
        name="Foreign Contact STO",
    )

    response = client.post(
        "/station-contacts/",
        json={
            "station_id": foreign_station_id,
            "type": "phone",
            "value": "+380501234567",
        },
    )

    assert response.status_code == 403


def test_read_station_contacts(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    _create_contact(auth_client, station_id, "+380501111111")
    _create_contact(auth_client, station_id, "+380502222222")

    response = client.get("/station-contacts/")

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["limit"] == 20
    assert data["offset"] == 0


def test_read_station_contacts_filters_by_station_id(
        auth_client, second_auth_client
):
    client, _user = auth_client
    first_station_id = _create_station(auth_client)
    second_station_id = _create_station(
        second_auth_client,
        name="Second Contact STO",
    )

    _create_contact(auth_client, first_station_id, "+380501111111")
    _create_contact(
        second_auth_client,
        second_station_id,
        "+380502222222",
    )

    response = client.get(
        "/station-contacts/",
        params={"station_id": first_station_id},
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["station_id"] == first_station_id


def test_read_station_contacts_respects_pagination(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    for index in range(3):
        _create_contact(
            auth_client,
            station_id,
            f"+38050123456{index}",
        )

    response = client.get(
        "/station-contacts/",
        params={"limit": 2, "offset": 1},
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 1


def test_read_station_contact_by_id(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)
    created = _create_contact(auth_client, station_id)

    response = client.get(f"/station-contacts/{created['id']}")

    assert response.status_code == 200, response.text
    assert response.json()["id"] == created["id"]
    assert response.json()["value"] == "+380501234567"


def test_read_station_contact_not_found(client):
    response = client.get("/station-contacts/999999")

    assert response.status_code == 404
    assert response.json()["message"] == "Station contact not found"


def test_update_station_contact_requires_auth(auth_client):
    owner_client, _user = auth_client
    station_id = _create_station(auth_client)
    created = _create_contact(auth_client, station_id)

    response = owner_client.put(
        f"/station-contacts/{created['id']}",
        json={"value": "+380509999999"},
    )

    assert response.status_code == 200

    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as anonymous_client:
        response = anonymous_client.put(
            f"/station-contacts/{created['id']}",
            json={"value": "+380508888888"},
        )

    assert response.status_code == 401


def test_update_station_contact_success(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)
    created = _create_contact(auth_client, station_id)

    response = client.put(
        f"/station-contacts/{created['id']}",
        json={
            "type": "email",
            "value": "service@example.com",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["type"] == "email"
    assert data["value"] == "service@example.com"


def test_update_station_contact_not_found(auth_client):
    client, _user = auth_client

    response = client.put(
        "/station-contacts/999999",
        json={"value": "+380509999999"},
    )

    assert response.status_code == 404


def test_update_station_contact_forbidden_for_foreign_station(
        auth_client, second_auth_client
):
    client, _user = auth_client
    foreign_station_id = _create_station(
        second_auth_client,
        name="Foreign Update Contact STO",
    )
    created = _create_contact(
        second_auth_client,
        foreign_station_id,
    )

    response = client.put(
        f"/station-contacts/{created['id']}",
        json={"value": "+380509999999"},
    )

    assert response.status_code == 403


def test_delete_station_contact_requires_auth(auth_client):
    owner_client, _user = auth_client
    station_id = _create_station(auth_client)
    created = _create_contact(auth_client, station_id)

    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as anonymous_client:
        response = anonymous_client.delete(
            f"/station-contacts/{created['id']}"
        )

    assert response.status_code == 401


def test_delete_station_contact_success(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)
    created = _create_contact(auth_client, station_id)

    response = client.delete(f"/station-contacts/{created['id']}")

    assert response.status_code == 200, response.text
    assert response.json() == {"id": created["id"]}

    follow_up = client.get(f"/station-contacts/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_station_contact_not_found(auth_client):
    client, _user = auth_client

    response = client.delete("/station-contacts/999999")

    assert response.status_code == 404


def test_delete_station_contact_forbidden_for_foreign_station(
        auth_client, second_auth_client
):
    client, _user = auth_client
    foreign_station_id = _create_station(
        second_auth_client,
        name="Foreign Delete Contact STO",
    )
    created = _create_contact(
        second_auth_client,
        foreign_station_id,
    )

    response = client.delete(f"/station-contacts/{created['id']}")

    assert response.status_code == 403


def test_create_station_contact_validates_fields(auth_client):
    client, _user = auth_client
    station_id = _create_station(auth_client)

    response = client.post(
        "/station-contacts/",
        json={
            "station_id": station_id,
            "type": "",
            "value": "",
        },
    )

    assert response.status_code == 422


def test_read_station_contact_returns_translated_not_found_message(
        auth_client,
):
    client, _user = auth_client

    response = client.get(
        "/station-contacts/999999",
        headers={"accept-language": "uk"},
    )

    assert response.status_code == 404
    assert response.json()["message"] != "Station contact not found"


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


def test_manager_can_manage_station_contacts(
        auth_client,
        second_auth_client,
        db_session,
):
    """An assigned Manager can create, update and delete station contacts."""
    owner_client, _owner = auth_client
    manager_client, manager_user = second_auth_client

    station_id = _create_station(
        auth_client,
        name="Manager Contacts STO",
    )

    _assign_station_role(
        db_session,
        station_id=station_id,
        user_id=manager_user["id"],
        role_name="Manager",
    )

    # Manager can create a contact.
    created = manager_client.post(
        "/station-contacts/",
        json={
            "station_id": station_id,
            "type": "phone",
            "value": "+380501234567",
        },
    )
    assert created.status_code == 201, created.text
    contact_id = created.json()["id"]

    # Manager can update the contact.
    updated = manager_client.put(
        f"/station-contacts/{contact_id}",
        json={"value": "+380509999999"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["value"] == "+380509999999"

    # Manager can delete the contact.
    deleted = manager_client.delete(
        f"/station-contacts/{contact_id}",
    )
    assert deleted.status_code == 200, deleted.text

    # The contact no longer exists.
    assert owner_client.get(
        f"/station-contacts/{contact_id}",
    ).status_code == 404


def test_cashier_cannot_manage_station_contacts(
        auth_client,
        second_auth_client,
        db_session,
):
    """An assigned Cashier cannot create, update or delete station contacts."""
    owner_client, _owner = auth_client
    cashier_client, cashier_user = second_auth_client

    station_id = _create_station(
        auth_client,
        name="Cashier Contacts STO",
    )
    existing_contact = _create_contact(
        auth_client,
        station_id,
    )

    _assign_station_role(
        db_session,
        station_id=station_id,
        user_id=cashier_user["id"],
        role_name="Cashier",
    )

    # Cashier cannot create a contact.
    created = cashier_client.post(
        "/station-contacts/",
        json={
            "station_id": station_id,
            "type": "phone",
            "value": "+380501111111",
        },
    )
    assert created.status_code == 403, created.text

    # Cashier cannot update an existing contact.
    updated = cashier_client.put(
        f"/station-contacts/{existing_contact['id']}",
        json={"value": "+380509999999"},
    )
    assert updated.status_code == 403, updated.text

    # Cashier cannot delete an existing contact.
    deleted = cashier_client.delete(
        f"/station-contacts/{existing_contact['id']}",
    )
    assert deleted.status_code == 403, deleted.text

    # The original contact must remain unchanged.
    unchanged = owner_client.get(
        f"/station-contacts/{existing_contact['id']}",
    )
    assert unchanged.status_code == 200, unchanged.text
    assert unchanged.json()["value"] == "+380501234567"
