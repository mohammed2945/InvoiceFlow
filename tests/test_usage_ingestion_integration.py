def _seed_plan_customer(client, customer_id: str):
    client.post(
        "/api/plans",
        json={
            "id": "growth",
            "version": "v1",
            "name": "Growth",
            "base_price_cents": 2000,
            "included_usage": 10,
            "overage_price_cents": 50,
        },
    )
    client.post(
        "/api/customers",
        json={
            "id": customer_id,
            "name": "Integration Co",
            "email": "int@test.example",
            "plan_id": "growth",
            "plan_version": "v1",
            "timezone": "UTC",
            "billing_cycle_day": 1,
        },
    )


def test_duplicate_retry_does_not_inflate_invoice_usage(client):
    customer_id = "cus_usage_integration"
    _seed_plan_customer(client, customer_id)

    event = {
        "customer_id": customer_id,
        "event_type": "compute",
        "quantity": 25,
        "timestamp": "2026-05-10T09:30:00Z",
        "source": "worker",
    }
    assert client.post("/api/usage-events", json=event).status_code == 201
    assert client.post("/api/usage-events", json=event).status_code == 200

    period = {
        "customer_id": customer_id,
        "billing_period_start": "2026-05-01T00:00:00Z",
        "billing_period_end": "2026-06-01T00:00:00Z",
    }
    preview = client.post("/api/invoices/preview", json=period)
    assert preview.status_code == 200
    assert preview.json()["total_usage_quantity"] == 25


def test_separate_minutes_aggregate_for_invoice(client):
    customer_id = "cus_usage_integration_2"
    _seed_plan_customer(client, customer_id)

    for ts in ("2026-05-10T10:00:00Z", "2026-05-10T10:02:00Z"):
        resp = client.post(
            "/api/usage-events",
            json={
                "customer_id": customer_id,
                "event_type": "compute",
                "quantity": 10,
                "timestamp": ts,
                "source": "worker",
            },
        )
        assert resp.status_code == 201

    period = {
        "customer_id": customer_id,
        "billing_period_start": "2026-05-01T00:00:00Z",
        "billing_period_end": "2026-06-01T00:00:00Z",
    }
    preview = client.post("/api/invoices/preview", json=period)
    assert preview.status_code == 200
    assert preview.json()["total_usage_quantity"] == 20
