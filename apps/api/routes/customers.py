from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.db import get_db
from apps.api.schemas import CustomerCreate, CustomerResponse
from apps.api.services.customer_service import (
    CustomerNotFoundError,
    PlanNotFoundError,
    create_customer,
    get_customer,
)

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse, status_code=201)
def post_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    try:
        customer = create_customer(db, payload)
    except PlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
def fetch_customer(customer_id: str, db: Session = Depends(get_db)):
    try:
        customer = get_customer(db, customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return customer
