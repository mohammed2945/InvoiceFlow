import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from apps.api.models import Customer, Plan
from apps.api.schemas import CustomerCreate


class CustomerNotFoundError(Exception):
    pass


class PlanNotFoundError(Exception):
    pass


def create_customer(db: Session, payload: CustomerCreate) -> Customer:
    plan = (
        db.query(Plan)
        .filter(Plan.id == payload.plan_id, Plan.version == payload.plan_version)
        .first()
    )
    if plan is None:
        raise PlanNotFoundError(
            f"Plan {payload.plan_id} version {payload.plan_version} not found"
        )

    customer_id = payload.id or f"cus_{uuid.uuid4().hex[:12]}"
    customer = Customer(
        id=customer_id,
        name=payload.name,
        email=payload.email,
        plan_id=payload.plan_id,
        plan_version=payload.plan_version,
        timezone=payload.timezone,
        billing_cycle_day=payload.billing_cycle_day,
        webhook_url=payload.webhook_url,
        created_at=datetime.now(timezone.utc),
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_customer(db: Session, customer_id: str) -> Customer:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer is None:
        raise CustomerNotFoundError(f"Customer {customer_id} not found")
    return customer
