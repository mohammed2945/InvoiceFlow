# Pricing Model

## Plan identity

A plan is uniquely identified by **`plan_id` + `plan_version`**. Together they represent an immutable pricing version.

Examples:

| plan_id | version | Meaning |
|---------|---------|---------|
| `starter` | `v2` | Current starter pricing |
| `legacy` | `v1` | Grandfathered legacy pricing |
| `enterprise` | `v3` | Current enterprise pricing |

## Customer assignment

Each customer stores:

- `plan_id`
- `plan_version`

Billing always resolves pricing using **both** fields. Two customers on `enterprise` may bill differently if one is on `v2` and another on `v3`.

## Versioning rules

- New pricing is published by creating a new plan row with the same `plan_id` and a new `version`
- Existing customers remain on their assigned version until migrated
- Invoice preview/finalize must never use `plan_id` alone

## API

- Create: `POST /api/plans` with `id` and `version`
- Read: `GET /api/plans/{plan_id}/{version}`
