import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from apps.api.models import UsageEvent
from apps.api.schemas import CreateUsageEventRequest
from apps.api.services.customer_service import CustomerNotFoundError, get_customer
from packages.observability.logging import get_logger, log_event
from packages.observability.metrics import increment

logger = get_logger(__name__)


@dataclass(frozen=True)
class UsageIngestionResult:
    event: UsageEvent
    status: str
    idempotency_key: str


def _usage_metric_tags(
    customer_id: str,
    event_type: str,
    source: str,
    extra: list[str] | None = None,
) -> list[str]:
    tags = [
        f"customer_id:{customer_id}",
        f"event_type:{event_type}",
        f"source:{source}",
    ]
    if extra:
        tags.extend(extra)
    return tags


def _ensure_utc(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def round_timestamp_to_minute(timestamp: datetime) -> datetime:
    ts = _ensure_utc(timestamp)
    rounded = ts.replace(second=0, microsecond=0)
    if ts.second >= 30:
        rounded += timedelta(minutes=1)
    return rounded


def compute_idempotency_key(
    customer_id: str,
    event_type: str,
    source: str,
    timestamp: datetime,
) -> str:
    minute_bucket = round_timestamp_to_minute(timestamp)
    material = (
        f"{customer_id}:{event_type}:{source}:"
        f"{minute_bucket.strftime('%Y-%m-%dT%H:%M:%S')}"
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def ingest_usage_event(db: Session, payload: CreateUsageEventRequest) -> UsageIngestionResult:
    try:
        get_customer(db, payload.customer_id)
    except CustomerNotFoundError:
        increment(
            "invoice.usage.ingestion.error",
            extra_tags=_usage_metric_tags(
                payload.customer_id,
                payload.event_type,
                payload.source,
                ["reason:customer_not_found"],
            ),
        )
        raise

    idempotency_key = compute_idempotency_key(
        payload.customer_id,
        payload.event_type,
        payload.source,
        payload.timestamp,
    )
    existing = (
        db.query(UsageEvent)
        .filter(UsageEvent.idempotency_key == idempotency_key)
        .first()
    )
    if existing is not None:
        increment(
            "invoice.usage.deduplicated.count",
            extra_tags=_usage_metric_tags(
                payload.customer_id,
                payload.event_type,
                payload.source,
            ),
        )
        log_event(
            logger,
            "info",
            "usage_event_deduplicated",
            customer_id=payload.customer_id,
            event_type=payload.event_type,
            quantity=payload.quantity,
            source=payload.source,
            idempotency_key=idempotency_key,
            timestamp=payload.timestamp.isoformat(),
            status="duplicate",
            usage_event_id=existing.id,
        )
        return UsageIngestionResult(
            event=existing,
            status="duplicate",
            idempotency_key=idempotency_key,
        )

    event_id = f"evt_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    event = UsageEvent(
        id=event_id,
        customer_id=payload.customer_id,
        event_type=payload.event_type,
        quantity=payload.quantity,
        timestamp=payload.timestamp,
        source=payload.source,
        idempotency_key=idempotency_key,
        received_at=now,
        deduplicated=False,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    increment(
        "invoice.usage.ingested.count",
        extra_tags=_usage_metric_tags(
            payload.customer_id,
            payload.event_type,
            payload.source,
        ),
    )
    log_event(
        logger,
        "info",
        "usage_event_ingested",
        customer_id=payload.customer_id,
        event_type=payload.event_type,
        quantity=payload.quantity,
        source=payload.source,
        idempotency_key=idempotency_key,
        timestamp=payload.timestamp.isoformat(),
        status="created",
        usage_event_id=event_id,
    )
    return UsageIngestionResult(
        event=event,
        status="created",
        idempotency_key=idempotency_key,
    )
