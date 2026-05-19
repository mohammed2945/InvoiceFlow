def _seed_plan_customer_and_usage(client):
    client.post(
        "/api/plans",
        json={
            "id": "pro",
            "version": "v1",
            "name": "Pro",
            "base_price_cents": 3000,
            "included_usage": 100,
            "overage_price_cents": 25,
        },
    )
    client.post(
        "/api/customers",
        json={
            "id": "cus_invoice_test",
            "name": "Invoice Test",
            "email": "invoice@test.example",
            "plan_id": "pro",
            "plan_version": "v1",
            "timezone": "UTC",
            "billing_cycle_day": 1,
        },
    )
    for qty, ts in [(40, "2026-05-05T12:00:00Z"), (80, "2026-05-10T12:00:00Z")]:
        client.post(
            "/api/usage-events",
            json={
                "customer_id": "cus_invoice_test",
                "event_type": "compute",
                "quantity": qty,
                "timestamp": ts,
                "source": "test",
            },
        )


def test_invoice_preview_and_finalize_with_overage(client):
    _seed_plan_customer_and_usage(client)

    period = {
        "customer_id": "cus_invoice_test",
        "billing_period_start": "2026-05-01T00:00:00Z",
        "billing_period_end": "2026-06-01T00:00:00Z",
    }

    preview = client.post("/api/invoices/preview", json=period)
    assert preview.status_code == 200
    preview_body = preview.json()
    assert preview_body["total_usage_quantity"] == 120
    assert preview_body["subtotal_cents"] == 3500
    assert preview_body["total_cents"] == 3500

    line_types = {item["type"] for item in preview_body["line_items"]}
    assert "base_fee" in line_types
    assert "usage_overage" in line_types

    finalize = client.post("/api/invoices/finalize", json=period)
    assert finalize.status_code == 201
    invoice = finalize.json()
    assert invoice["status"] == "finalized"
    assert invoice["total_cents"] == 3500
    assert len(invoice["line_items"]) >= 2
