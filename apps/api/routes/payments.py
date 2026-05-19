from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.db import get_db
from apps.api.schemas import PaymentRecordRequest, PaymentResponse
from apps.api.services.payment_service import InvoiceNotFoundError, record_payment

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/record", response_model=PaymentResponse, status_code=201)
def post_payment_record(payload: PaymentRecordRequest, db: Session = Depends(get_db)):
    try:
        payment = record_payment(db, payload)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return payment
