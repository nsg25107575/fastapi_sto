def test_get_stations(client):
    response = client.get("/stations/")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0


def test_get_station(client):
    response = client.get("/stations/1")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert "name" in data
    assert "address" in data


def test_get_station_not_found(client):
    response = client.get("/stations/999999")

    assert response.status_code == 404


def test_create_station(client):
    response = client.post(
        "/stations/",
        params={
            "name": "Test Station",
            "address": "Test Address"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Test Station"
    assert data["address"] == "Test Address"
    assert "id" in data


def test_create_duplicate_station(client):
    params = {
        "name": "Duplicate Station",
        "address": "Duplicate Address"
    }

    response = client.post(
        "/stations/",
        params=params
    )

    assert response.status_code == 200

    response = client.post(
        "/stations/",
        params=params
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Станция с таким названием и адресом уже существует"
    )


def test_update_station(client):
    response = client.put(
        "/stations/1",
        params={
            "name": "Updated Station",
            "address": "Updated Address"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["name"] == "Updated Station"
    assert data["address"] == "Updated Address"


def test_delete_station(client):
    response = client.post(
        "/stations/",
        params={
            "name": "Station For Delete",
            "address": "Address For Delete"
        }
    )

    assert response.status_code == 200

    station_id = response.json()["id"]

    response = client.delete(
        f"/stations/{station_id}"
    )

    assert response.status_code == 200
    assert response.json() == station_id

    response = client.get(
        f"/stations/{station_id}"
    )

    assert response.status_code == 404
