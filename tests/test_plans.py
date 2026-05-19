def test_create_and_fetch_plan(client):
    create_resp = client.post(
        "/api/plans",
        json={
            "id": "enterprise",
            "version": "v2",
            "name": "Enterprise",
            "base_price_cents": 50000,
            "included_usage": 10000,
            "overage_price_cents": 5,
            "currency": "usd",
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["id"] == "enterprise"
    assert created["version"] == "v2"

    get_resp = client.get("/api/plans/enterprise/v2")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["base_price_cents"] == 50000
    assert fetched["included_usage"] == 10000
