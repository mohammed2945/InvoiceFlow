import time

from sqlalchemy import func
from sqlalchemy.orm import Session

from apps.api.models import Invoice, Payment, UsageEvent
from apps.api.schemas import DashboardResponse
from apps.api.services.customer_service import CustomerNotFoundError, get_customer
from packages.observability.logging import get_logger, log_event
from packages.observability.metrics import increment, timing

logger = get_logger(__name__)

OPEN_STATUSES = {"draft", "finalized", "sent", "failed"}


def get_dashboard(db: Session, customer_id: str) -> DashboardResponse:
    start = time.perf_counter()
    try:
        get_customer(db, customer_id)
    except CustomerNotFoundError:
        raise

    total_invoices = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.customer_id == customer_id)
        .scalar()
        or 0
    )
    paid_invoices = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.customer_id == customer_id, Invoice.status == "paid")
        .scalar()
        or 0
    )
    open_invoices = (
        db.query(func.count(Invoice.id))
        .filter(
            Invoice.customer_id == customer_id,
            Invoice.status.in_(OPEN_STATUSES),
        )
        .scalar()
        or 0
    )
    total_revenue = (
        db.query(func.coalesce(func.sum(Invoice.total_cents), 0))
        .filter(Invoice.customer_id == customer_id, Invoice.status == "paid")
        .scalar()
        or 0
    )
    total_usage = (
        db.query(func.coalesce(func.sum(UsageEvent.quantity), 0))
        .filter(UsageEvent.customer_id == customer_id)
        .scalar()
        or 0
    )
    pending_payment_count = (
        db.query(func.count(Payment.id))
        .join(Invoice, Payment.invoice_id == Invoice.id)
        .filter(Invoice.customer_id == customer_id, Payment.status == "pending")
        .scalar()
        or 0
    )

    elapsed_ms = (time.perf_counter() - start) * 1000
    increment("invoice.dashboard.request.count", extra_tags=[f"customer_id:{customer_id}"])
    timing("invoice.dashboard.latency_ms", elapsed_ms)

    response = DashboardResponse(
        customer_id=customer_id,
        total_invoices=int(total_invoices),
        paid_invoices=int(paid_invoices),
        open_invoices=int(open_invoices),
        total_revenue_cents=int(total_revenue),
        total_usage_quantity=int(total_usage),
        pending_payment_count=int(pending_payment_count),
    )

    log_event(
        logger,
        "info",
        "dashboard_loaded",
        customer_id=customer_id,
        total_invoices=response.total_invoices,
        paid_invoices=response.paid_invoices,
        open_invoices=response.open_invoices,
        total_revenue_cents=response.total_revenue_cents,
    )
    return response
