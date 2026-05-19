def test_dashboard_totals(client):
    client.post(
        "/api/plans",
        json={
            "id": "dash_plan",
            "version": "v1",
            "name": "Dash Plan",
            "base_price_cents": 1000,
            "included_usage": 1000,
            "overage_price_cents": 1,
        },
    )
    client.post(
        "/api/customers",
        json={
            "id": "cus_dash_test",
            "name": "Dash Test",
            "email": "dash@test.example",
            "plan_id": "dash_plan",
            "plan_version": "v1",
            "timezone": "UTC",
            "billing_cycle_day": 1,
        },
    )

    client.post(
        "/api/usage-events",
        json={
            "customer_id": "cus_dash_test",
            "event_type": "storage",
            "quantity": 30,
            "timestamp": "2026-05-02T00:00:00Z",
            "source": "test",
        },
    )
    client.post(
        "/api/usage-events",
        json={
            "customer_id": "cus_dash_test",
            "event_type": "storage",
            "quantity": 20,
            "timestamp": "2026-05-03T00:00:00Z",
            "source": "test",
        },
    )

    period = {
        "customer_id": "cus_dash_test",
        "billing_period_start": "2026-05-01T00:00:00Z",
        "billing_period_end": "2026-06-01T00:00:00Z",
    }

    paid_invoice = client.post("/api/invoices/finalize", json=period).json()
    client.post(
        "/api/payments/record",
        json={
            "invoice_id": paid_invoice["id"],
            "status": "succeeded",
            "amount_cents": paid_invoice["total_cents"],
        },
    )

    client.post("/api/invoices/finalize", json=period)

    client.post(
        "/api/payments/record",
        json={
            "invoice_id": paid_invoice["id"],
            "status": "pending",
            "amount_cents": 100,
        },
    )

    resp = client.get("/api/dashboard/cus_dash_test")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_invoices"] == 2
    assert data["paid_invoices"] == 1
    assert data["open_invoices"] == 1
    assert data["total_revenue_cents"] == paid_invoice["total_cents"]
    assert data["total_usage_quantity"] == 50
    assert data["pending_payment_count"] == 1
