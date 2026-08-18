# Domain Layer

**Layer:** innermost (no imports from application, adapters, or interfaces)

## Purpose

Pure domain models, value objects, temporal logic, and validation rules
for the EU Tariff Compliance and Validation Engine.

## Invariants

- Zero I/O. No network, no database, no filesystem.
- All models are frozen (immutable) with extra="forbid" (strict).
- Money, rates, and quantities use `Decimal`. Never `float`.
- All dates use `datetime.date`. No naive datetimes.
- Domain models are unsuffixed (e.g. `Measure`, not `MeasureModel`).

## Modules

| Module | Contents |
|--------|----------|
| `errors.py` | Exception hierarchy rooted at `TariffEngineError` |
| `models.py` | All Pydantic domain models and enumerations |

## Key Entities

- **ValidityPeriod**: half-open interval `[valid_from, valid_to)` with containment and overlap checks
- **GoodsNomenclatureCode**: validated 10-digit TARIC code with HS/CN/TARIC accessors
- **GoodsNomenclature**: a node in the nomenclature hierarchy
- **GeographicalArea**: country, group, or region
- **DutyExpression**: how a duty is expressed (ad valorem, specific, flat per item, etc.)
- **MeasureComponent**: duty amount and units
- **MeasureCondition**: prerequisites for a measure (certificates, documents)
- **Footnote**: clarifying or limiting text
- **LegalActReference**: link to EUR-Lex via CELEX ID and ELI URI
- **MeasureType**: classification of a customs measure
- **Measure**: the central entity tying everything together

## 2026 Low Value Consignment Regime

The `DutyExpressionKind` enum includes two types for the 2026 regime:

- `FLAT_PER_ITEM`: EUR 3 flat customs duty per item (effective 1 July 2026)
- `HANDLING_FEE`: per-parcel fee that is not a customs duty (by November 2026)

Both are temporary until the Customs Data Hub is operational.
