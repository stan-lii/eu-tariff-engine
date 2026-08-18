# Phase 2 Step 1: Domain Models

## Summary

Define the core domain entities as frozen Pydantic v2 models in the domain layer.
No SQL, no I/O, no database. Pure domain logic only.

## Entities

- ValidityPeriod (value object)
- GoodsNomenclature (nomenclature node)
- GeographicalArea (country, group, region)
- DutyExpression and DutyExpressionKind (including 2026 low value consignment types)
- MeasureComponent (duty amount and units)
- MeasureCondition and MeasureConditionComponent
- Footnote
- LegalActReference (CELEX and ELI)
- Measure (central entity)
- MeasureType

## Constraints

- All models: frozen=True, extra="forbid"
- Decimal for money, rates, quantities. Never float.
- date for all dates. No naive datetimes.
- Domain layer has zero I/O, zero imports from outer layers.

## Exit Criteria

- All models pass mypy strict.
- All models pass ruff.
- Unit tests pass offline.
- make check green.
