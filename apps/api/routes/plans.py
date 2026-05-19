from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.db import get_db
from apps.api.schemas import PlanCreate, PlanResponse
from apps.api.services.plan_service import PlanNotFoundError, create_plan, get_plan

router = APIRouter(prefix="/api/plans", tags=["plans"])


@router.post("", response_model=PlanResponse, status_code=201)
def post_plan(payload: PlanCreate, db: Session = Depends(get_db)):
    plan = create_plan(db, payload)
    return plan


@router.get("/{plan_id}/{version}", response_model=PlanResponse)
def fetch_plan(plan_id: str, version: str, db: Session = Depends(get_db)):
    try:
        plan = get_plan(db, plan_id, version)
    except PlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return plan
