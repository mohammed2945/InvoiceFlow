# Usage Ingestion

## Endpoint

`POST /api/usage-events`

### Request body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customer_id` | string | yes | Customer identifier |
| `event_type` | string | yes | Usage category (e.g. `api_call`) |
| `quantity` | integer | yes | Positive usage amount |
| `timestamp` | datetime | yes | When usage occurred |
| `source` | string | no | Originating system (default `api`) |

### Responses

| Status | `status` field | Meaning |
|--------|----------------|---------|
| `201` | `created` | New usage event stored |
| `200` | `duplicate` | Matching idempotency key already exists |
| `404` | — | Customer not found |

Response body:

```json
{
  "status": "created",
  "usage_event_id": "evt_...",
  "idempotency_key": "..."
}
```

## Idempotency

Customer SDKs and gateways may retry `POST /api/usage-events` on timeouts or ambiguous responses. InvoiceFlow deduplicates retries using an **idempotency key** derived from:

- `customer_id`
- `event_type`
- `source`
- `timestamp` rounded to the nearest minute

A retry with the same key returns `200` and the original `usage_event_id` without inserting a second row.

Duplicate responses during client retries are **expected** and should not be treated as errors.

## Downstream usage

Usage events within `[billing_period_start, billing_period_end)` are summed when generating invoice previews and finalized invoices. Only stored (non-deduplicated) events contribute to billing totals.

## Metrics

| Metric | When emitted |
|--------|----------------|
| `invoice.usage.ingested.count` | New event stored |
| `invoice.usage.deduplicated.count` | Duplicate key detected |
| `invoice.usage.ingestion.error` | Validation or customer lookup failure |

Tags include `customer_id`, `event_type`, `source`, plus default `service`, `env`, and `version`.

### Monitoring guidance

- `invoice.usage.deduplicated.count` should usually stay **low relative to** `invoice.usage.ingested.count` during steady-state traffic.
- A spike in deduplicated events may indicate aggressive client retries or misconfigured SDK retry policies.
- Correlate with `invoice.usage.ingestion.error` for ingestion health.

## Logs

Structured events:

| Event | Description |
|-------|-------------|
| `usage_event_ingested` | New event stored (`status: created`) |
| `usage_event_deduplicated` | Duplicate key matched (`status: duplicate`) |

Both include `customer_id`, `event_type`, `quantity`, `source`, `idempotency_key`, and `timestamp`.

## Data model

`UsageEvent` fields include `idempotency_key` (unique, indexed) and `deduplicated` (boolean, default `false` on stored rows).
