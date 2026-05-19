import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from apps.api.models import Invoice, Payment
from apps.api.schemas import PaymentRecordRequest
from packages.observability.logging import get_logger, log_event
from packages.observability.metrics import gauge, increment

logger = get_logger(__name__)


class InvoiceNotFoundError(Exception):
    pass


def record_payment(db: Session, payload: PaymentRecordRequest) -> Payment:
    invoice = db.query(Invoice).filter(Invoice.id == payload.invoice_id).first()
    if invoice is None:
        raise InvoiceNotFoundError(f"Invoice {payload.invoice_id} not found")

    now = datetime.now(timezone.utc)
    payment = Payment(
        id=f"pay_{uuid.uuid4().hex[:12]}",
        invoice_id=payload.invoice_id,
        provider=payload.provider,
        provider_payment_id=payload.provider_payment_id,
        status=payload.status,
        amount_cents=payload.amount_cents,
        created_at=now,
        updated_at=now,
    )
    db.add(payment)

    if payload.status == "succeeded":
        invoice.status = "paid"
        invoice.paid_at = now
        increment("invoice.payment.succeeded.count")
        gauge("invoice.revenue.recognized_cents", payload.amount_cents)
        log_event(
            logger,
            "info",
            "invoice_marked_paid",
            customer_id=invoice.customer_id,
            invoice_id=invoice.id,
            payment_id=payment.id,
            amount_cents=payload.amount_cents,
        )
    elif payload.status == "pending":
        increment("invoice.payment.pending.count")
    elif payload.status == "failed":
        increment("invoice.payment.failed.count")

    db.commit()
    db.refresh(payment)

    log_event(
        logger,
        "info",
        "payment_recorded",
        customer_id=invoice.customer_id,
        invoice_id=invoice.id,
        payment_id=payment.id,
        status=payload.status,
        amount_cents=payload.amount_cents,
    )
    return payment
