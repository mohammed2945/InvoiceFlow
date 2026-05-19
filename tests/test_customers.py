def test_create_and_fetch_customer(client):
    plan_resp = client.post(
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
    assert plan_resp.status_code == 201

    create_resp = client.post(
        "/api/customers",
        json={
            "name": "Acme Corp",
            "email": "billing@acme.example",
            "plan_id": "starter",
            "plan_version": "v1",
            "timezone": "UTC",
            "billing_cycle_day": 1,
        },
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    customer_id = body["id"]
    assert body["name"] == "Acme Corp"
    assert body["plan_id"] == "starter"

    get_resp = client.get(f"/api/customers/{customer_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == customer_id
    assert fetched["email"] == "billing@acme.example"
