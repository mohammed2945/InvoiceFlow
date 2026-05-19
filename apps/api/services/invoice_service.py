import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from apps.api.models import Invoice, InvoiceLineItem, UsageEvent
from apps.api.schemas import InvoicePeriodRequest, InvoicePreviewResponse
from apps.api.services.customer_service import CustomerNotFoundError, get_customer
from apps.api.services.plan_service import PlanNotFoundError, get_plan
from packages.observability.logging import get_logger, log_event
from packages.observability.metrics import gauge, increment

logger = get_logger(__name__)

OPEN_STATUSES = {"draft", "finalized", "sent", "failed"}


@dataclass
class BillingCalculation:
    total_usage: int
    subtotal_cents: int
    total_cents: int
    currency: str
    line_items: list[dict]


def _sum_usage(
    db: Session,
    customer_id: str,
    period_start: datetime,
    period_end: datetime,
) -> int:
    total = (
        db.query(func.coalesce(func.sum(UsageEvent.quantity), 0))
        .filter(
            UsageEvent.customer_id == customer_id,
            UsageEvent.timestamp >= period_start,
            UsageEvent.timestamp < period_end,
        )
        .scalar()
    )
    return int(total or 0)


def _calculate_billing(
    db: Session,
    customer_id: str,
    plan_id: str,
    plan_version: str,
    period_start: datetime,
    period_end: datetime,
) -> BillingCalculation:
    plan = get_plan(db, plan_id, plan_version)
    total_usage = _sum_usage(db, customer_id, period_start, period_end)
    overage_units = max(0, total_usage - plan.included_usage)
    base_amount = plan.base_price_cents
    overage_amount = overage_units * plan.overage_price_cents

    line_items = [
        {
            "type": "base_fee",
            "description": f"{plan.name} base subscription",
            "quantity": 1,
            "unit_price_cents": plan.base_price_cents,
            "amount_cents": base_amount,
        },
    ]
    if overage_units > 0:
        line_items.append(
            {
                "type": "usage_overage",
                "description": f"Usage overage ({overage_units} units)",
                "quantity": overage_units,
                "unit_price_cents": plan.overage_price_cents,
                "amount_cents": overage_amount,
            }
        )

    subtotal = base_amount + overage_amount
    return BillingCalculation(
        total_usage=total_usage,
        subtotal_cents=subtotal,
        total_cents=subtotal,
        currency=plan.currency,
        line_items=line_items,
    )


def preview_invoice(db: Session, payload: InvoicePeriodRequest) -> InvoicePreviewResponse:
    try:
        customer = get_customer(db, payload.customer_id)
    except CustomerNotFoundError:
        raise

    calc = _calculate_billing(
        db,
        customer.id,
        customer.plan_id,
        customer.plan_version,
        payload.billing_period_start,
        payload.billing_period_end,
    )

    increment("invoice.generated.count", extra_tags=["mode:preview"])
    log_event(
        logger,
        "info",
        "invoice_preview_generated",
        customer_id=customer.id,
        billing_period_start=payload.billing_period_start.isoformat(),
        billing_period_end=payload.billing_period_end.isoformat(),
        total_cents=calc.total_cents,
        total_usage_quantity=calc.total_usage,
    )

    from apps.api.schemas import InvoiceLineItemPreview

    return InvoicePreviewResponse(
        customer_id=customer.id,
        billing_period_start=payload.billing_period_start,
        billing_period_end=payload.billing_period_end,
        subtotal_cents=calc.subtotal_cents,
        total_cents=calc.total_cents,
        currency=calc.currency,
        total_usage_quantity=calc.total_usage,
        line_items=[InvoiceLineItemPreview(**item) for item in calc.line_items],
    )


def finalize_invoice(db: Session, payload: InvoicePeriodRequest) -> Invoice:
    try:
        customer = get_customer(db, payload.customer_id)
    except CustomerNotFoundError:
        raise

    try:
        get_plan(db, customer.plan_id, customer.plan_version)
    except PlanNotFoundError:
        raise

    calc = _calculate_billing(
        db,
        customer.id,
        customer.plan_id,
        customer.plan_version,
        payload.billing_period_start,
        payload.billing_period_end,
    )

    now = datetime.now(timezone.utc)
    invoice_id = f"inv_{uuid.uuid4().hex[:12]}"
    invoice = Invoice(
        id=invoice_id,
        customer_id=customer.id,
        billing_period_start=payload.billing_period_start,
        billing_period_end=payload.billing_period_end,
        status="finalized",
        subtotal_cents=calc.subtotal_cents,
        total_cents=calc.total_cents,
        currency=calc.currency,
        created_at=now,
        finalized_at=now,
        paid_at=None,
    )
    db.add(invoice)
    db.flush()

    for item in calc.line_items:
        line = InvoiceLineItem(
            id=f"li_{uuid.uuid4().hex[:12]}",
            invoice_id=invoice_id,
            type=item["type"],
            description=item["description"],
            quantity=item["quantity"],
            unit_price_cents=item["unit_price_cents"],
            amount_cents=item["amount_cents"],
        )
        db.add(line)

    db.commit()
    db.refresh(invoice)

    increment("invoice.finalized.count")
    gauge("invoice.revenue.expected_cents", calc.total_cents)
    log_event(
        logger,
        "info",
        "invoice_finalized",
        customer_id=customer.id,
        invoice_id=invoice_id,
        total_cents=calc.total_cents,
        status="finalized",
    )
    return invoice
