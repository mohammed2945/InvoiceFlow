# Service Catalog

## invoice-api

| Property | Value |
|----------|-------|
| **Service name** | `invoice-api` |
| **Type** | HTTP API |
| **Language** | Python 3.11+ |
| **Framework** | FastAPI |
| **Default port** | 8000 |

### Owned routes

| Route | Purpose |
|-------|---------|
| `POST /api/customers` | Create customer |
| `GET /api/customers/{customer_id}` | Fetch customer |
| `POST /api/plans` | Create plan version |
| `GET /api/plans/{plan_id}/{version}` | Fetch plan version |
| `POST /api/usage-events` | Ingest usage |
| `POST /api/invoices/preview` | Preview billing |
| `POST /api/invoices/finalize` | Finalize invoice |
| `POST /api/payments/record` | Record payment |
| `GET /api/dashboard/{customer_id}` | Revenue dashboard |
| `GET /health` | Health check |

### Key metrics

| Metric | Description |
|--------|-------------|
| `invoice.api.request.count` | API requests |
| `invoice.api.request.latency_ms` | Request latency |
| `invoice.api.request.error` | API errors |
| `invoice.usage.ingested.count` | Usage events stored |
| `invoice.usage.deduplicated.count` | Duplicate idempotency keys |
| `invoice.usage.ingestion.error` | Usage ingestion failures |
| `invoice.generated.count` | Invoice previews |
| `invoice.finalized.count` | Finalized invoices |
| `invoice.revenue.expected_cents` | Expected revenue on finalize |
| `invoice.revenue.recognized_cents` | Revenue on successful payment |
| `invoice.payment.succeeded.count` | Successful payments |
| `invoice.payment.pending.count` | Pending payments |
| `invoice.payment.failed.count` | Failed payments |
| `invoice.dashboard.request.count` | Dashboard requests |
| `invoice.dashboard.latency_ms` | Dashboard latency |

### Structured log events

- `usage_event_ingested`
- `usage_event_deduplicated`
- `invoice_preview_generated`
- `invoice_finalized`
- `payment_recorded`
- `invoice_marked_paid`
- `dashboard_loaded`
- `api_request_completed`
- `api_request_failed`
