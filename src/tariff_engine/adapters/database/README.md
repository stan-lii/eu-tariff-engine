# Database Adapter

**Layer:** adapters (imports domain, never imported by domain or application)

## Purpose

SQLAlchemy schema definitions, repository classes, and temporal query
functions for the Neon Postgres bitemporal database.

## Bitemporal Model

Every versioned entity carries four columns:

| Column | Type | Meaning |
|--------|------|---------|
| `valid_from` | DATE | Start of legal validity (inclusive) |
| `valid_to` | DATE, nullable | End of legal validity (exclusive). NULL = open ended. |
| `recorded_at` | TIMESTAMPTZ | When the system recorded this version |
| `superseded_at` | TIMESTAMPTZ, nullable | When this version was replaced. NULL = current. |

**Rules:**
- No UPDATE to data columns. Supersede and insert instead.
- No DELETE. Set superseded_at instead.
- All writes go through `record_measure_version()` with provenance.

## Tables

**Bitemporal (versioned):** measures, goods_nomenclatures,
geographical_areas, duty_expressions, measure_types, footnotes

**Child (versioned with parent measure):** measure_components,
measure_conditions, measure_condition_components, measure_footnotes,
measure_excluded_areas

## Temporal Query Pattern

"As of legal date D, as known on date E":
```sql
WHERE valid_from <= D
  AND (valid_to IS NULL OR valid_to > D)
  AND recorded_at <= E
  AND (superseded_at IS NULL OR superseded_at > E)
```

## Modules

| Module | Contents |
|--------|----------|
| `schema.py` | SQLAlchemy Table definitions, indexes, metadata |
