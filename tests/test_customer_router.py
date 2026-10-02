"""Tests for POST /customer (anonymous geolocation capture)."""


def test_create_customer_success(client):
    response = client.post(
        "/customer/",
        json={
            "lat": 50.4501,
            "lng": 30.5234,
            "public_data": {"browser": "test-agent"},
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data["id"], int)
    assert data["public_data"] == {"browser": "test-agent"}
    assert "device_hash" in data
    assert len(data["device_hash"]) == 36


def test_create_customer_generates_unique_device_hash(client):
    payload = {
        "lat": 50.4501,
        "lng": 30.5234,
        "public_data": {},
    }

    first = client.post("/customer/", json=payload).json()
    second = client.post("/customer/", json=payload).json()

    assert first["device_hash"] != second["device_hash"]


def test_create_customer_requires_lat_lng(client):
    response = client.post(
        "/customer/",
        json={"public_data": {}},
    )

    assert response.status_code == 422
