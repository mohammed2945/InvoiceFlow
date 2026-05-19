#!/usr/bin/env python3
"""Seed demo customers, plans, usage events, and sample invoices."""

import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.db import SessionLocal, init_db
from apps.api.models import Customer, Invoice, Plan, UsageEvent
from apps.api.schemas import CustomerCreate, InvoicePeriodRequest, PlanCreate
from apps.api.services.customer_service import create_customer
from apps.api.services.invoice_service import finalize_invoice
from apps.api.services.plan_service import create_plan
from apps.api.services.usage_ingestion_service import compute_idempotency_key

NOW = datetime.now(timezone.utc)
PERIOD_START = NOW.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
PERIOD_END = (PERIOD_START + timedelta(days=32)).replace(day=1)


def seed_plans(db):
    plans = [
        PlanCreate(
            id="starter",
            version="v2",
            name="Starter",
            base_price_cents=2900,
            included_usage=500,
            overage_price_cents=5,
        ),
        PlanCreate(
            id="enterprise",
            version="v3",
            name="Enterprise",
            base_price_cents=49900,
            included_usage=50000,
            overage_price_cents=2,
        ),
        PlanCreate(
            id="legacy",
            version="v1",
            name="Legacy Grandfathered",
            base_price_cents=9900,
            included_usage=2000,
            overage_price_cents=3,
        ),
    ]
    for plan in plans:
        create_plan(db, plan)


def seed_customers(db):
    customers = [
        CustomerCreate(
            id="cus_small_001",
            name="SmallCo",
            email="billing@smallco.example",
            plan_id="starter",
            plan_version="v2",
            timezone="America/New_York",
            billing_cycle_day=15,
        ),
        CustomerCreate(
            id="cus_large_001",
            name="MegaCorp",
            email="enterprise@megacorp.example",
            plan_id="enterprise",
            plan_version="v3",
            timezone="UTC",
            billing_cycle_day=1,
        ),
        CustomerCreate(
            id="cus_legacy_001",
            name="LegacyIndustries",
            email="ap@legacyind.example",
            plan_id="legacy",
            plan_version="v1",
            timezone="America/Chicago",
            billing_cycle_day=10,
        ),
        CustomerCreate(
            id="cus_asia_001",
            name="AsiaRetail",
            email="finance@asiaretail.example",
            plan_id="starter",
            plan_version="v2",
            timezone="Asia/Kolkata",
            billing_cycle_day=1,
        ),
        CustomerCreate(
            id="cus_webhook_001",
            name="WebhookHeavyCo",
            email="ops@webhookheavy.example",
            plan_id="enterprise",
            plan_version="v3",
            timezone="UTC",
            billing_cycle_day=1,
            webhook_url="https://hooks.webhookheavy.example/invoiceflow",
        ),
    ]
    for customer in customers:
        create_customer(db, customer)


def _ingest_events(db, customer_id: str, count: int, base_qty: int):
    for i in range(count):
        event_type = random.choice(["api_call", "storage_gb", "compute_minute"])
        ts = PERIOD_START + timedelta(hours=i % 720)
        event = UsageEvent(
            id=f"evt_seed_{customer_id}_{i}",
            customer_id=customer_id,
            event_type=event_type,
            quantity=base_qty + random.randint(0, 10),
            timestamp=ts,
            source="seed_script",
            idempotency_key=compute_idempotency_key(
                customer_id, event_type, "seed_script", ts
            ),
            received_at=NOW,
            deduplicated=False,
        )
        db.merge(event)
    db.commit()


def seed_usage(db):
    _ingest_events(db, "cus_small_001", 12, 5)
    _ingest_events(db, "cus_large_001", 200, 250)
    _ingest_events(db, "cus_legacy_001", 25, 15)
    _ingest_events(db, "cus_asia_001", 40, 20)
    _ingest_events(db, "cus_webhook_001", 150, 80)


def seed_sample_invoices(db):
    for customer_id in ("cus_small_001", "cus_legacy_001"):
        finalize_invoice(
            db,
            InvoicePeriodRequest(
                customer_id=customer_id,
                billing_period_start=PERIOD_START,
                billing_period_end=PERIOD_END,
            ),
        )


def main():
    init_db()
    db = SessionLocal()
    try:
        seed_plans(db)
        seed_customers(db)
        seed_usage(db)
        seed_sample_invoices(db)
        print("Demo data seeded successfully.")
        print(f"  Plans: {db.query(Plan).count()}")
        print(f"  Customers: {db.query(Customer).count()}")
        print(f"  Usage events: {db.query(UsageEvent).count()}")
        print(f"  Invoices: {db.query(Invoice).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
