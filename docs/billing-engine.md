# Billing Engine

## Flow

1. Load customer → resolve `plan_id` + `plan_version`
2. Sum `UsageEvent.quantity` for the billing period
3. Compute line items and totals
4. Preview (read-only) or finalize (persist invoice + line items)

## Pricing components

### Base fee

One line item of type `base_fee`:

- Quantity: 1
- Amount: `plan.base_price_cents`

### Included usage

Each plan defines `included_usage` units included in the base fee.

### Overage

```
overage_units = max(0, total_usage - included_usage)
overage_amount = overage_units * plan.overage_price_cents
```

When `overage_units > 0`, a `usage_overage` line item is added.

### Total

```
subtotal_cents = base_fee + overage_amount
total_cents = subtotal_cents
```

Discount and tax line item types exist in the schema for future use but are not applied in the baseline.

## Invoice finalization

`POST /api/invoices/finalize` creates:

- An `Invoice` with `status = finalized` and `finalized_at` set
- `InvoiceLineItem` rows for each computed component

Metrics:

- `invoice.finalized.count`
- `invoice.revenue.expected_cents` (gauge set to invoice total)

## Preview

`POST /api/invoices/preview` runs the same calculation without writing to the database. Emits `invoice.generated.count` with tag `mode:preview`.
