from apps.api.models import UsageEvent


def _seed_customer(client, customer_id: str, email: str):
    client.post(
        "/api/plans",
        json={
            "id": "starter",
            "version": "v1",
            "name": "Starter",
            "base_price_cents": 1000,
            "included_usage": 100,
            "overage_price_cents": 10,
        },
    )
    client.post(
        "/api/customers",
        json={
            "id": customer_id,
            "name": customer_id,
            "email": email,
            "plan_id": "starter",
            "plan_version": "v1",
            "timezone": "UTC",
            "billing_cycle_day": 1,
        },
    )


def test_single_usage_event_created(client, db_session):
    _seed_customer(client, "cus_usage_1", "u1@test.example")
    payload = {
        "customer_id": "cus_usage_1",
        "event_type": "api_call",
        "quantity": 3,
        "timestamp": "2026-05-01T10:15:00Z",
        "source": "sdk",
    }
    resp = client.post("/api/usage-events", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "created"
    assert body["usage_event_id"]
    assert body["idempotency_key"]

    stored = db_session.query(UsageEvent).filter(UsageEvent.customer_id == "cus_usage_1").all()
    assert len(stored) == 1
    assert stored[0].deduplicated is False


def test_exact_duplicate_request_deduplicated(client, db_session):
    _seed_customer(client, "cus_usage_2", "u2@test.example")
    payload = {
        "customer_id": "cus_usage_2",
        "event_type": "api_call",
        "quantity": 7,
        "timestamp": "2026-05-01T11:20:00Z",
        "source": "sdk",
    }
    first = client.post("/api/usage-events", json=payload)
    second = client.post("/api/usage-events", json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
    assert second.json()["usage_event_id"] == first.json()["usage_event_id"]
    assert second.json()["idempotency_key"] == first.json()["idempotency_key"]

    assert db_session.query(UsageEvent).filter(UsageEvent.customer_id == "cus_usage_2").count() == 1


def test_different_customers_not_deduplicated(client, db_session):
    _seed_customer(client, "cus_usage_a", "a@test.example")
    _seed_customer(client, "cus_usage_b", "b@test.example")
    base = {
        "event_type": "api_call",
        "quantity": 4,
        "timestamp": "2026-05-01T12:00:00Z",
        "source": "sdk",
    }
    first = client.post(
        "/api/usage-events",
        json={**base, "customer_id": "cus_usage_a"},
    )
    second = client.post(
        "/api/usage-events",
        json={**base, "customer_id": "cus_usage_b"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["idempotency_key"] != second.json()["idempotency_key"]
    assert db_session.query(UsageEvent).count() == 2


def test_different_event_types_not_deduplicated(client, db_session):
    _seed_customer(client, "cus_usage_3", "u3@test.example")
    shared = {
        "customer_id": "cus_usage_3",
        "quantity": 2,
        "timestamp": "2026-05-01T13:00:00Z",
        "source": "sdk",
    }
    first = client.post(
        "/api/usage-events",
        json={**shared, "event_type": "api_call"},
    )
    second = client.post(
        "/api/usage-events",
        json={**shared, "event_type": "storage_gb"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert db_session.query(UsageEvent).filter(UsageEvent.customer_id == "cus_usage_3").count() == 2


def test_different_minutes_not_deduplicated(client, db_session):
    _seed_customer(client, "cus_usage_4", "u4@test.example")
    base = {
        "customer_id": "cus_usage_4",
        "event_type": "api_call",
        "quantity": 5,
        "source": "sdk",
    }
    first = client.post(
        "/api/usage-events",
        json={**base, "timestamp": "2026-05-01T14:00:10Z"},
    )
    second = client.post(
        "/api/usage-events",
        json={**base, "timestamp": "2026-05-01T14:01:10Z"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert db_session.query(UsageEvent).filter(UsageEvent.customer_id == "cus_usage_4").count() == 2
