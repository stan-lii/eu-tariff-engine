"""Domain models for the EU Tariff Engine.

All models in this module are:
- frozen=True (immutable after creation)
- extra="forbid" (reject unknown fields)
- Pure domain objects with zero I/O

Money, rates, and quantities use Decimal. Never float.
All dates use datetime.date. No naive datetimes.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum, unique

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

# ---------------------------------------------------------------------------
# Base configuration shared by all domain models
# ---------------------------------------------------------------------------


class DomainModel(BaseModel):
    """Base class for all domain models.

    Enforces frozen (immutable) and extra="forbid" (strict) across the board.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


@unique
class GeographicalAreaKind(StrEnum):
    """Classification of a geographical area in the TARIC system.

    TARIC uses a numeric code: 0 = country, 1 = group, 2 = region.
    """

    COUNTRY = "country"
    GROUP = "group"
    REGION = "region"


@unique
class TradeMovementCode(StrEnum):
    """Direction of trade a measure applies to."""

    IMPORT = "import"
    EXPORT = "export"
    BOTH = "both"


@unique
class DutyExpressionKind(StrEnum):
    """Classification of duty expression types.

    Standard TARIC types plus the two new types required by the
    2026 low value consignment regime:

    - FLAT_PER_ITEM: a flat monetary amount per item (e.g. EUR 3)
      that is neither ad valorem nor per unit of the goods.
      Introduced by the abolition of the EUR 150 customs duty relief
      effective 1 July 2026.

    - HANDLING_FEE: a per-parcel fee collected by member states that
      is not a customs duty. Required by November 2026, level set by
      a Commission delegated act, reassessed every two years.
      Both are temporary and remain in force until the Customs Data Hub
      is operational.
    """

    AD_VALOREM = "ad_valorem"
    SPECIFIC = "specific"
    COMPOUND = "compound"
    SUPPLEMENTARY = "supplementary"
    FLAT_PER_ITEM = "flat_per_item"
    HANDLING_FEE = "handling_fee"


@unique
class RegulationRole(StrEnum):
    """Role of a regulation in the TARIC system.

    Maps to the regulationRoleType field in the TARIC XML.
    """

    BASE = "1"
    MODIFICATION = "4"
    PROVISIONAL_ANTI_DUMPING = "2"
    DEFINITIVE_ANTI_DUMPING = "3"
    FULL_TEMPORARY_STOP = "8"


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


class ValidityPeriod(DomainModel):
    """A half-open time interval [valid_from, valid_to).

    valid_to is None for open-ended periods (still in force).
    """

    valid_from: date
    valid_to: date | None = None

    @field_validator("valid_to")
    @classmethod
    def valid_to_not_before_valid_from(cls, v: date | None, info: ValidationInfo) -> date | None:
        """Ensure valid_to is not before valid_from when both are present."""
        if v is not None:
            valid_from = info.data.get("valid_from")
            if valid_from is not None and v < valid_from:
                msg = f"valid_to ({v}) must not be before valid_from ({valid_from})"
                raise ValueError(msg)
        return v

    def contains(self, d: date) -> bool:
        """Return True if date d falls within this period."""
        if d < self.valid_from:
            return False
        return not (self.valid_to is not None and d >= self.valid_to)

    def overlaps(self, other: "ValidityPeriod") -> bool:
        """Return True if this period overlaps with another."""
        if self.valid_to is not None and self.valid_to <= other.valid_from:
            return False
        return not (other.valid_to is not None and other.valid_to <= self.valid_from)


class GoodsNomenclatureCode(DomainModel):
    """A 10-digit TARIC goods nomenclature code.

    Structure:
    - Digits 1 to 6: HS code (Harmonized System, WCO)
    - Digits 7 to 8: CN code (Combined Nomenclature, EU)
    - Digits 9 to 10: TARIC subheading
    """

    code: str = Field(
        ...,
        min_length=10,
        max_length=10,
        pattern=r"^\d{10}$",
        description="10-digit TARIC goods nomenclature code",
    )

    @property
    def hs_heading(self) -> str:
        """First 4 digits: HS heading."""
        return self.code[:4]

    @property
    def hs_code(self) -> str:
        """First 6 digits: HS subheading."""
        return self.code[:6]

    @property
    def cn_code(self) -> str:
        """First 8 digits: Combined Nomenclature code."""
        return self.code[:8]

    @property
    def taric_code(self) -> str:
        """Full 10-digit TARIC code."""
        return self.code

    def __str__(self) -> str:
        return self.code


# ---------------------------------------------------------------------------
# Domain entities
# ---------------------------------------------------------------------------


class GoodsNomenclature(DomainModel):
    """A node in the goods nomenclature hierarchy.

    Represents a product classification at any level of the
    HS / CN / TARIC hierarchy. The indent_number reflects
    the depth in the nomenclature tree.
    """

    sid: int = Field(..., description="TARIC system identifier")
    goods_nomenclature_code: GoodsNomenclatureCode
    product_line_suffix: str = Field(
        ...,
        min_length=2,
        max_length=2,
        pattern=r"^\d{2}$",
        description="Product line suffix, e.g. '80' for declarable codes",
    )
    indent_number: int = Field(..., ge=0, description="Depth in the nomenclature tree")
    description: str = Field(..., min_length=1, description="Description of the goods")
    validity: ValidityPeriod
    statistical_indicator: bool = Field(
        default=False,
        description="Whether this code is used for statistical purposes",
    )


class GeographicalArea(DomainModel):
    """A country, country group, or region in the TARIC system.

    Country IDs follow ISO 3166. Group and region IDs are
    TARIC-specific (e.g. '1011' for Erga Omnes).
    """

    sid: int = Field(..., description="TARIC system identifier")
    geographical_area_id: str = Field(
        ...,
        min_length=2,
        max_length=4,
        description="ISO country code or TARIC group/region code",
    )
    kind: GeographicalAreaKind
    description: str = Field(..., min_length=1, description="Name of the geographical area")
    validity: ValidityPeriod
    parent_group_sid: int | None = Field(
        default=None,
        description="SID of the parent geographical area group, if any",
    )


class DutyExpression(DomainModel):
    """A duty expression type from the TARIC system.

    Controls how a duty is expressed: whether an amount is permitted
    or mandatory, whether a measurement unit applies, etc.
    """

    duty_expression_id: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="TARIC duty expression ID, e.g. '01'",
    )
    description: str
    kind: DutyExpressionKind = Field(
        ...,
        description="Semantic classification of the duty expression",
    )
    duty_amount_applicable: bool = Field(
        default=True,
        description="Whether a duty amount is applicable",
    )
    measurement_unit_applicable: bool = Field(
        default=False,
        description="Whether a measurement unit is applicable",
    )
    monetary_unit_applicable: bool = Field(
        default=False,
        description="Whether a monetary unit is applicable",
    )
    validity: ValidityPeriod


class MeasureComponent(DomainModel):
    """A duty component of a measure.

    Contains the duty amount, the expression type, and the units.
    Multiple components combine to form compound duties like
    '4.5% + EUR 0.3 per item'.
    """

    duty_expression_id: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="References a DutyExpression",
    )
    duty_amount: Decimal | None = Field(
        default=None, description="Duty amount (rate or flat value)"
    )
    monetary_unit_code: str | None = Field(
        default=None,
        max_length=3,
        description="Currency code, e.g. 'EUR'",
    )
    measurement_unit_code: str | None = Field(
        default=None,
        max_length=3,
        description="Measurement unit, e.g. 'DTN' (100 kg), 'NAR' (items)",
    )
    measurement_unit_qualifier_code: str | None = Field(
        default=None,
        max_length=1,
        description="Qualifier, e.g. 'A' (total alcohol)",
    )


class MeasureConditionComponent(DomainModel):
    """A duty component within a measure condition.

    Structurally identical to MeasureComponent but semantically
    belongs to a condition rather than the measure itself.
    """

    duty_expression_id: str = Field(..., min_length=2, max_length=2)
    duty_amount: Decimal | None = None
    monetary_unit_code: str | None = Field(default=None, max_length=3)
    measurement_unit_code: str | None = Field(default=None, max_length=3)
    measurement_unit_qualifier_code: str | None = Field(default=None, max_length=1)


class MeasureCondition(DomainModel):
    """A condition attached to a measure.

    Conditions determine when a measure applies based on
    certificates, documents, or other prerequisites.
    Multiple conditions with the same condition_code are
    ordered by sequence_number.
    """

    sid: int = Field(..., description="TARIC system identifier")
    condition_code: str = Field(
        ...,
        min_length=1,
        max_length=2,
        description="Condition code, e.g. 'A', 'B', 'Y'",
    )
    sequence_number: int = Field(..., ge=0, description="Order within the condition group")
    duty_amount: Decimal | None = None
    monetary_unit_code: str | None = Field(default=None, max_length=3)
    measurement_unit_code: str | None = Field(default=None, max_length=3)
    measurement_unit_qualifier_code: str | None = Field(default=None, max_length=1)
    action_code: str | None = Field(
        default=None,
        max_length=3,
        description="Action to take when condition is met, e.g. '01'",
    )
    certificate_type: str | None = Field(
        default=None,
        max_length=1,
        description="Certificate type code",
    )
    certificate_code: str | None = Field(
        default=None,
        max_length=3,
        description="Certificate code",
    )
    components: tuple[MeasureConditionComponent, ...] = Field(
        default=(),
        description="Duty components for this condition",
    )


class Footnote(DomainModel):
    """A footnote attached to a nomenclature code or measure.

    Footnotes either clarify nomenclature or limit the
    application of a measure.
    """

    footnote_type: str = Field(
        ...,
        min_length=2,
        max_length=3,
        description="Footnote type, e.g. 'TN', 'CD', 'MH'",
    )
    footnote_id: str = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Footnote identifier",
    )
    description: str = Field(..., min_length=1, description="Footnote text")
    validity: ValidityPeriod


class LegalActReference(DomainModel):
    """Reference to a legal act in the Official Journal of the EU.

    Links a measure to its legal basis using both CELEX (the
    document identifier in EUR-Lex) and ELI (the European
    Legislation Identifier URI).

    The regulation_id follows TARIC encoding: e.g. 'R1501880'
    where R = regulation, 15 = year, 01880 = number.
    """

    regulation_id: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="TARIC regulation ID, e.g. 'R1501880'",
    )
    regulation_role: RegulationRole = Field(..., description="Role of the regulation")
    celex_id: str | None = Field(
        default=None,
        description="CELEX identifier, e.g. '32015R0001'",
    )
    eli_uri: str | None = Field(
        default=None,
        description="ELI URI, e.g. 'http://data.europa.eu/eli/...'",
    )
    official_journal_id: str | None = Field(
        default=None,
        max_length=5,
        description="Official Journal number, e.g. 'L 145'",
    )
    journal_page: str | None = Field(
        default=None,
        max_length=4,
        description="Page in the Official Journal",
    )
    date_published: date | None = Field(default=None, description="Publication date")
    description: str | None = Field(default=None, description="Free text description of the act")


class MeasureType(DomainModel):
    """Classification of a customs measure.

    Covers tariff measures (levies, anti-dumping duties) and
    non-tariff measures (quantitative restrictions, prohibitions).
    """

    measure_type_id: str = Field(
        ...,
        min_length=1,
        max_length=6,
        description="Measure type ID, e.g. '103' (third country duty)",
    )
    description: str = Field(..., min_length=1, description="Description of the measure type")
    trade_movement_code: TradeMovementCode
    validity: ValidityPeriod


class Measure(DomainModel):
    """The central entity: a customs measure.

    A measure is the application, during a certain period of time,
    of an aspect of EU tariff and commercial legislation to goods
    imported from or exported to a certain origin/destination.

    Components, conditions, excluded areas, and footnotes are
    stored as tuples (immutable sequences) to maintain the
    frozen guarantee.
    """

    sid: int = Field(..., description="TARIC system identifier")
    measure_type_id: str = Field(
        ...,
        min_length=1,
        max_length=6,
        description="References a MeasureType",
    )
    goods_nomenclature_code: GoodsNomenclatureCode | None = Field(
        default=None,
        description="The goods this measure applies to",
    )
    geographical_area_id: str = Field(
        ...,
        min_length=2,
        max_length=4,
        description="Origin/destination area",
    )
    additional_code_type: str | None = Field(default=None, max_length=1)
    additional_code_id: str | None = Field(default=None, max_length=3)
    quota_order_number: str | None = Field(
        default=None,
        max_length=6,
        description="Quota order number if this is a quota measure",
    )
    validity: ValidityPeriod
    regulation: LegalActReference = Field(..., description="The regulation creating this measure")
    justification_regulation: LegalActReference | None = Field(
        default=None,
        description="Justification regulation, if different from creating",
    )
    stopped: bool = Field(
        default=False,
        description="Whether this measure is currently stopped",
    )
    components: tuple[MeasureComponent, ...] = Field(
        default=(),
        description="Duty components defining the rate",
    )
    conditions: tuple[MeasureCondition, ...] = Field(
        default=(),
        description="Conditions under which this measure applies",
    )
    excluded_geographical_areas: tuple[str, ...] = Field(
        default=(),
        description="Geographical area IDs excluded from this measure",
    )
    footnotes: tuple[Footnote, ...] = Field(
        default=(),
        description="Footnotes associated with this measure",
    )
