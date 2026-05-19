from datetime import datetime, timezone

from sqlalchemy.orm import Session

from apps.api.models import Plan
from apps.api.schemas import PlanCreate


class PlanNotFoundError(Exception):
    pass


def create_plan(db: Session, payload: PlanCreate) -> Plan:
    existing = (
        db.query(Plan)
        .filter(Plan.id == payload.id, Plan.version == payload.version)
        .first()
    )
    if existing:
        return existing

    plan = Plan(
        id=payload.id,
        version=payload.version,
        name=payload.name,
        base_price_cents=payload.base_price_cents,
        included_usage=payload.included_usage,
        overage_price_cents=payload.overage_price_cents,
        currency=payload.currency,
        created_at=datetime.now(timezone.utc),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_plan(db: Session, plan_id: str, version: str) -> Plan:
    plan = (
        db.query(Plan)
        .filter(Plan.id == plan_id, Plan.version == version)
        .first()
    )
    if plan is None:
        raise PlanNotFoundError(f"Plan {plan_id} version {version} not found")
    return plan
