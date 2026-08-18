"""Exception hierarchy for the EU Tariff Engine.

Every exception in the system descends from TariffEngineError.
Adapters translate all third-party exceptions into this hierarchy.
No third-party exception (httpx, sqlalchemy, etc.) escapes an adapter.
"""


class TariffEngineError(Exception):
    """Root exception for the EU Tariff Engine."""


class SourceError(TariffEngineError):
    """Error originating from an external data source.

    Subclasses may be marked as transient for retry eligibility.
    """

    transient: bool = False

    def __init__(self, message: str, *, transient: bool = False) -> None:
        super().__init__(message)
        self.transient = transient


class ValidationError(TariffEngineError):
    """Domain or business rule validation failure.

    Not to be confused with pydantic.ValidationError. This is for
    tariff-specific validation: rate bounds, period continuity,
    mutually exclusive measure types, nomenclature code validity.
    """


class TemporalError(TariffEngineError):
    """Bitemporal invariant violation.

    Raised when a temporal operation would break the append-only,
    supersession-based model: overlapping validity without supersession,
    mutation of a recorded_at timestamp, or a missing provenance argument.
    """


class ExtractionError(TariffEngineError):
    """LLM extraction or parsing failure.

    Raised when structured extraction from a document or source
    produces output that fails the strict Pydantic output model.
    """


class ConfigurationError(TariffEngineError):
    """Invalid or missing configuration.

    Raised at startup when required settings are absent or contradictory.
    """


class BudgetError(TariffEngineError):
    """Token or cost budget exceeded.

    Raised when a per-run token budget or the persisted monthly
    spend accumulator would be breached by the next LLM call.
    """
