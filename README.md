# InvoiceFlow

InvoiceFlow is a B2B billing and usage metering platform for SaaS companies. It supports customer onboarding, versioned pricing plans, usage event ingestion, invoice generation, payment recording, and a revenue dashboard.

This repository provides a production-like baseline API intended for observability and incident-debugging exercises with Datadog and GitHub.

## Features

- Create customers and assign pricing plans (by `plan_id` + `plan_version`)
- Ingest usage events with idempotent deduplication
- Preview and finalize invoices with base fee + overage calculation
- Record payments and mark invoices paid
- Customer revenue dashboard
- Datadog-friendly JSON logs and DogStatsD metrics

## Requirements

- Python 3.11+
- pip

## Setup

```bash
pip install -r requirements.txt
```

## Run API

```bash
uvicorn apps.api.main:app --reload
```

The API listens on `http://localhost:8000` by default. Health check: `GET /health`.

Optional environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./invoiceflow.db` | SQLAlchemy database URL |
| `DD_SERVICE` | `invoice-api` | Service name in logs/metrics |
| `DD_ENV` | `local` | Environment tag |
| `DD_VERSION` | `local` | Version tag |
| `DD_AGENT_HOST` | `localhost` | DogStatsD host |
| `DD_DOGSTATSD_PORT` | `8125` | DogStatsD port |

## Run tests

```bash
pytest
```

## Seed demo data

With the API stopped (or using a fresh DB file):

```bash
python scripts/seed_demo_data.py
```

Seeded customers: `cus_small_001`, `cus_large_001`, `cus_legacy_001`, `cus_asia_001`, `cus_webhook_001`.

## Run traffic

Start the API, seed data, then:

```bash
python traffic/normal_user_flow.py
python traffic/usage_high_volume.py
```

Set `INVOICEFLOW_API_URL` to target a different host (default `http://localhost:8000`). Seed data before traffic; `usage_high_volume.py` sends 500 events for `cus_large_001` in one minute bucket.

## API overview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/customers` | Create customer |
| GET | `/api/customers/{customer_id}` | Get customer |
| POST | `/api/plans` | Create plan version |
| GET | `/api/plans/{plan_id}/{version}` | Get plan version |
| POST | `/api/usage-events` | Ingest usage event (201 created / 200 duplicate) |
| POST | `/api/invoices/preview` | Preview invoice |
| POST | `/api/invoices/finalize` | Finalize invoice |
| POST | `/api/payments/record` | Record payment |
| GET | `/api/dashboard/{customer_id}` | Customer dashboard |

See `docs/` for architecture, billing engine, and runbooks.
