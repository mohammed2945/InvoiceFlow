from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.db import get_db
from apps.api.schemas import DashboardResponse
from apps.api.services.customer_service import CustomerNotFoundError
from apps.api.services.dashboard_service import get_dashboard

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/{customer_id}", response_model=DashboardResponse)
def fetch_dashboard(customer_id: str, db: Session = Depends(get_db)):
    try:
        return get_dashboard(db, customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
