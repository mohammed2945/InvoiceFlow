from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.db import get_db
from apps.api.schemas import InvoicePeriodRequest, InvoicePreviewResponse, InvoiceResponse
from apps.api.services.customer_service import CustomerNotFoundError
from apps.api.services.invoice_service import finalize_invoice, preview_invoice
from apps.api.services.plan_service import PlanNotFoundError

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.post("/preview", response_model=InvoicePreviewResponse)
def post_invoice_preview(payload: InvoicePeriodRequest, db: Session = Depends(get_db)):
    try:
        return preview_invoice(db, payload)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/finalize", response_model=InvoiceResponse, status_code=201)
def post_invoice_finalize(payload: InvoicePeriodRequest, db: Session = Depends(get_db)):
    try:
        invoice = finalize_invoice(db, payload)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return invoice
