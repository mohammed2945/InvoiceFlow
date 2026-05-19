def test_payment_marks_invoice_paid(client):
    client.post(
        "/api/plans",
        json={
            "id": "basic",
            "version": "v1",
            "name": "Basic",
            "base_price_cents": 1500,
            "included_usage": 10,
            "overage_price_cents": 100,
        },
    )
    client.post(
        "/api/customers",
        json={
            "id": "cus_pay_test",
            "name": "Pay Test",
            "email": "pay@test.example",
            "plan_id": "basic",
            "plan_version": "v1",
            "timezone": "UTC",
            "billing_cycle_day": 1,
        },
    )

    period = {
        "customer_id": "cus_pay_test",
        "billing_period_start": "2026-05-01T00:00:00Z",
        "billing_period_end": "2026-06-01T00:00:00Z",
    }
    invoice_resp = client.post("/api/invoices/finalize", json=period)
    invoice = invoice_resp.json()

    payment_resp = client.post(
        "/api/payments/record",
        json={
            "invoice_id": invoice["id"],
            "provider_payment_id": "pi_test_123",
            "status": "succeeded",
            "amount_cents": invoice["total_cents"],
        },
    )
    assert payment_resp.status_code == 201

    dashboard = client.get("/api/dashboard/cus_pay_test")
    assert dashboard.status_code == 200
    assert dashboard.json()["paid_invoices"] == 1
    assert dashboard.json()["total_revenue_cents"] == invoice["total_cents"]
