from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from apps.api.db import get_db
from apps.api.schemas import CreateUsageEventRequest, UsageEventResponse
from apps.api.services.customer_service import CustomerNotFoundError
from apps.api.services.usage_ingestion_service import ingest_usage_event

router = APIRouter(prefix="/api/usage-events", tags=["usage"])


@router.post("", response_model=UsageEventResponse)
def post_usage_event(
    payload: CreateUsageEventRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        result = ingest_usage_event(db, payload)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    response.status_code = 201 if result.status == "created" else 200
    return UsageEventResponse(
        status=result.status,
        usage_event_id=result.event.id,
        idempotency_key=result.idempotency_key,
    )
