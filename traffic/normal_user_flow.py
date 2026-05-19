#!/usr/bin/env python3
"""Simulate normal API traffic against a running InvoiceFlow instance."""

import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone

import httpx

API_BASE = os.environ.get("INVOICEFLOW_API_URL", "http://localhost:8000").rstrip("/")

CUSTOMER_IDS = [
    "cus_small_001",
    "cus_large_001",
    "cus_legacy_001",
    "cus_asia_001",
    "cus_webhook_001",
]

PERIOD_START = datetime.now(timezone.utc).replace(
    day=1, hour=0, minute=0, second=0, microsecond=0
)
PERIOD_END = (PERIOD_START + timedelta(days=32)).replace(day=1)


def main():
    success = 0
    errors = 0
    client = httpx.Client(base_url=API_BASE, timeout=10.0)

    print(f"Traffic generator targeting {API_BASE}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            customer_id = random.choice(CUSTOMER_IDS)
            try:
                usage_resp = client.post(
                    "/api/usage-events",
                    json={
                        "customer_id": customer_id,
                        "event_type": "api_call",
                        "quantity": random.randint(1, 50),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source": "traffic_script",
                    },
                )
                if usage_resp.status_code == 201:
                    success += 1
                else:
                    errors += 1
                    print(f"usage-events failed: {usage_resp.status_code} {usage_resp.text}")

                preview_resp = client.post(
                    "/api/invoices/preview",
                    json={
                        "customer_id": customer_id,
                        "billing_period_start": PERIOD_START.isoformat(),
                        "billing_period_end": PERIOD_END.isoformat(),
                    },
                )
                if preview_resp.status_code == 200:
                    success += 1
                else:
                    errors += 1

                if random.random() < 0.15:
                    finalize_resp = client.post(
                        "/api/invoices/finalize",
                        json={
                            "customer_id": customer_id,
                            "billing_period_start": PERIOD_START.isoformat(),
                            "billing_period_end": PERIOD_END.isoformat(),
                        },
                    )
                    if finalize_resp.status_code == 201:
                        success += 1
                        invoice = finalize_resp.json()
                        if random.random() < 0.5:
                            pay_resp = client.post(
                                "/api/payments/record",
                                json={
                                    "invoice_id": invoice["id"],
                                    "provider_payment_id": f"pi_traffic_{random.randint(1000, 9999)}",
                                    "status": "succeeded",
                                    "amount_cents": invoice["total_cents"],
                                },
                            )
                            if pay_resp.status_code == 201:
                                success += 1
                            else:
                                errors += 1
                    else:
                        errors += 1

                dash_resp = client.get(f"/api/dashboard/{customer_id}")
                if dash_resp.status_code == 200:
                    success += 1
                else:
                    errors += 1

            except httpx.HTTPError as exc:
                errors += 1
                print(f"request error: {exc}")

            print(f"\rsuccess={success} errors={errors}", end="", flush=True)
            time.sleep(1.0)
    except KeyboardInterrupt:
        print(f"\nStopped. success={success} errors={errors}")
        sys.exit(0)


if __name__ == "__main__":
    main()
