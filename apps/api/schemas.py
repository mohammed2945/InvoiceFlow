from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerCreate(BaseModel):
    id: Optional[str] = None
    name: str
    email: EmailStr
    plan_id: str
    plan_version: str
    timezone: str = "UTC"
    billing_cycle_day: int = Field(ge=1, le=28)
    webhook_url: Optional[str] = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    plan_id: str
    plan_version: str
    timezone: str
    billing_cycle_day: int
    webhook_url: Optional[str]
    created_at: datetime


class PlanCreate(BaseModel):
    id: str
    version: str
    name: str
    base_price_cents: int = Field(ge=0)
    included_usage: int = Field(ge=0)
    overage_price_cents: int = Field(ge=0)
    currency: str = "usd"


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: str
    name: str
    base_price_cents: int
    included_usage: int
    overage_price_cents: int
    currency: str
    created_at: datetime


class CreateUsageEventRequest(BaseModel):
    customer_id: str
    event_type: str
    quantity: int = Field(gt=0)
    timestamp: datetime
    source: str = "api"


class UsageEventResponse(BaseModel):
    status: str
    usage_event_id: str
    idempotency_key: str


class InvoicePeriodRequest(BaseModel):
    customer_id: str
    billing_period_start: datetime
    billing_period_end: datetime


class InvoiceLineItemPreview(BaseModel):
    type: str
    description: str
    quantity: int
    unit_price_cents: int
    amount_cents: int


class InvoicePreviewResponse(BaseModel):
    customer_id: str
    billing_period_start: datetime
    billing_period_end: datetime
    subtotal_cents: int
    total_cents: int
    currency: str
    total_usage_quantity: int
    line_items: list[InvoiceLineItemPreview]


class InvoiceLineItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: str
    type: str
    description: str
    quantity: int
    unit_price_cents: int
    amount_cents: int


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    billing_period_start: datetime
    billing_period_end: datetime
    status: str
    subtotal_cents: int
    total_cents: int
    currency: str
    created_at: datetime
    finalized_at: Optional[datetime]
    paid_at: Optional[datetime]
    line_items: list[InvoiceLineItemResponse] = []


class PaymentRecordRequest(BaseModel):
    invoice_id: str
    provider_payment_id: Optional[str] = None
    status: str
    amount_cents: int = Field(ge=0)
    provider: str = "manual"


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: str
    provider: str
    provider_payment_id: Optional[str]
    status: str
    amount_cents: int
    created_at: datetime
    updated_at: datetime


class DashboardResponse(BaseModel):
    customer_id: str
    total_invoices: int
    paid_invoices: int
    open_invoices: int
    total_revenue_cents: int
    total_usage_quantity: int
    pending_payment_count: int
