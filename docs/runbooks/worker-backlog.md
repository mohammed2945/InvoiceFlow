# Runbook: Worker Backlog (Placeholder)

## Status

The baseline InvoiceFlow deployment does **not** include an async worker. Billing, webhooks, and batch jobs run synchronously in the API process.

A future worker service will handle:

- Customer webhook delivery
- Scheduled invoice generation
- Usage aggregation batches

## Future metrics (not yet implemented)

When the worker is added, monitor:

- `invoice.worker.queue.depth`
- `invoice.worker.job.processed.count`
- `invoice.worker.job.error.count`
- `invoice.worker.job.latency_ms`

## Current workaround

- Use `traffic/normal_user_flow.py` or cron-triggered API calls for batch-like behavior
- Check API logs and `invoice.finalized.count` for billing activity
