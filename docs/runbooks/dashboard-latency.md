# Runbook: Dashboard Latency

## Symptoms

- Slow dashboard loads for customers
- Elevated `invoice.dashboard.latency_ms`
- User reports on `GET /api/dashboard/{customer_id}`

## Investigation

1. Check `invoice.dashboard.latency_ms` in Datadog, grouped by `customer_id` tag
2. Check `invoice.dashboard.request.count` for traffic spikes
3. Identify affected `customer_id` values from logs (`dashboard_loaded` event)
4. Compare large vs small customers:
   - `cus_large_001` (MegaCorp) — high usage event volume
   - `cus_webhook_001` — many events

## Mitigations

- Verify database indexes on `usage_events.customer_id` and `invoices.customer_id`
- Consider caching dashboard aggregates (future enhancement)
- Scale API replicas if CPU-saturated

## Related metrics

- `invoice.api.request.latency_ms` (route `/api/dashboard/{customer_id}`)
- `invoice.usage.ingested.count` (ingestion volume driving aggregates)
