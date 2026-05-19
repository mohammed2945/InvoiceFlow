#!/usr/bin/env python3
"""High-volume usage ingestion against a running InvoiceFlow API."""

import os
import random
import sys
from datetime import datetime, timezone

import httpx

API_BASE = os.environ.get("INVOICEFLOW_API_URL", "http://localhost:8000").rstrip("/")
CUSTOMER_ID = "cus_large_001"
EVENT_TYPE = "api_call"
SOURCE = "high_volume_traffic"
EVENT_COUNT = 500


def main():
    client = httpx.Client(base_url=API_BASE, timeout=30.0)
    bucket = datetime.now(timezone.utc).replace(second=15, microsecond=0)
    created = 0
    duplicate = 0
    errors = 0

    print(f"Sending {EVENT_COUNT} usage events to {API_BASE}")
    print(f"customer_id={CUSTOMER_ID} event_type={EVENT_TYPE} minute_bucket={bucket.isoformat()}")

    for i in range(EVENT_COUNT):
        payload = {
            "customer_id": CUSTOMER_ID,
            "event_type": EVENT_TYPE,
            "quantity": random.randint(1, 100),
            "timestamp": bucket.isoformat(),
            "source": SOURCE,
        }
        try:
            resp = client.post("/api/usage-events", json=payload)
            if resp.status_code == 201:
                created += 1
            elif resp.status_code == 200 and resp.json().get("status") == "duplicate":
                duplicate += 1
            else:
                errors += 1
                print(f"unexpected response {resp.status_code}: {resp.text[:200]}")
        except httpx.HTTPError as exc:
            errors += 1
            print(f"request failed: {exc}")

    print(f"created={created} duplicate={duplicate} errors={errors}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
