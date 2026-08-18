"""Domain layer: Pydantic models, value objects, temporal logic, validation rules.

This layer has zero I/O, zero third-party clients, zero LLM calls.
It must be importable with no network and no database.
"""

from tariff_engine.domain.errors import (
    BudgetError,
    ConfigurationError,
    ExtractionError,
    SourceError,
    TariffEngineError,
    TemporalError,
    ValidationError,
)
from tariff_engine.domain.models import (
    DomainModel,
    DutyExpression,
    DutyExpressionKind,
    Footnote,
    GeographicalArea,
    GeographicalAreaKind,
    GoodsNomenclature,
    GoodsNomenclatureCode,
    LegalActReference,
    Measure,
    MeasureComponent,
    MeasureCondition,
    MeasureConditionComponent,
    MeasureType,
    RegulationRole,
    TradeMovementCode,
    ValidityPeriod,
)

__all__ = [
    "BudgetError",
    "ConfigurationError",
    "DomainModel",
    "DutyExpression",
    "DutyExpressionKind",
    "ExtractionError",
    "Footnote",
    "GeographicalArea",
    "GeographicalAreaKind",
    "GoodsNomenclature",
    "GoodsNomenclatureCode",
    "LegalActReference",
    "Measure",
    "MeasureComponent",
    "MeasureCondition",
    "MeasureConditionComponent",
    "MeasureType",
    "RegulationRole",
    "SourceError",
    "TariffEngineError",
    "TemporalError",
    "TradeMovementCode",
    "ValidationError",
    "ValidityPeriod",
]
