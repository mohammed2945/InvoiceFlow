# Runbook: Revenue Drop

## Symptoms

- Drop in recognized revenue
- Finance alerts on MRR / collected revenue
- `invoice.revenue.recognized_cents` flat or declining

## Investigation

1. **Recognized revenue**: `invoice.revenue.recognized_cents` (emitted on successful payment)
2. **Expected revenue**: `invoice.revenue.expected_cents` (emitted on invoice finalize)
3. **Payments**:
   - `invoice.payment.succeeded.count`
   - `invoice.payment.failed.count`
   - `invoice.payment.pending.count`
4. **Usage pipeline**:
   - `invoice.usage.ingested.count` — is usage still flowing?
   - `invoice.usage.ingestion.error` — customer validation failures?
5. **Finalization**: `invoice.finalized.count` — are invoices being created?

## Log queries

Search for:

- `invoice_finalized`
- `payment_recorded`
- `invoice_marked_paid`

Correlate by `customer_id` and `invoice_id`.

## Common causes

- Payment provider failures (`status: failed`)
- Fewer finalized invoices (billing job not run — manual finalize in baseline)
- Usage ingestion errors reducing billable usage
