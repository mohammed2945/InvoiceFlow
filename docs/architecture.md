# InvoiceFlow Architecture

## Overview

InvoiceFlow is a monolithic FastAPI service backed by a relational database. The baseline deployment runs as a single `invoice-api` process with SQLite for local development and a Postgres-compatible schema for production.

```
Clients / traffic scripts
        |
        v
+------------------+
|   invoice-api    |  FastAPI + middleware (metrics/logs)
+------------------+
        |
        v
+------------------+
|    Database      |  SQLite (local) / Postgres (prod)
+------------------+
```

## Components

### API service (`apps/api`)

- **Routes**: HTTP handlers for customers, plans, usage, invoices, payments, dashboard
- **Services**: Business logic layer (billing calculations, ingestion, payments)
- **Models**: SQLAlchemy ORM entities
- **Middleware**: Request count, latency, and error metrics per route

### Database

Stores customers, versioned plans, usage events, invoices, line items, and payments. Tables are created on startup for local development via `init_db()`.

### Usage ingestion

`POST /api/usage-events` validates the customer, deduplicates by idempotency key, and emits `invoice.usage.ingested.count` or `invoice.usage.deduplicated.count`.

### Invoice generation

Preview loads the customer's plan version, sums usage in the billing window, and calculates:

- Base subscription fee
- Overage units × per-unit overage price

Finalize persists an invoice in `finalized` status with line items.

### Payment recording

`POST /api/payments/record` creates a payment row. Successful payments mark the invoice `paid` and set `paid_at`.

### Dashboard

Aggregates invoice counts, recognized revenue, total usage quantity, and pending payments for a customer.

### Observability (`packages/observability`)

- JSON structured logs (Datadog-friendly fields)
- DogStatsD metrics with default `service`, `env`, and `version` tags

## Future extensions

- Async worker for webhooks and batch billing (not in baseline)
- Idempotent usage ingestion (next PR)
- Redis / Celery (not in baseline)
