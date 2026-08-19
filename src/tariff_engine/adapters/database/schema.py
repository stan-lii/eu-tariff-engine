"""Bitemporal database schema for the EU Tariff Engine.

All tables follow the append-only bitemporal model:
- valid_from / valid_to:  legal validity (business time)
- recorded_at / superseded_at: system knowledge (transaction time)

No UPDATE to data columns, no DELETE. Supersede instead.

Tables use snake_case plural per the constitution.
"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
)

metadata = MetaData()

# ---------------------------------------------------------------------------
# Bitemporal column factory
# ---------------------------------------------------------------------------


def _bitemporal_columns() -> list[Column]:  # type: ignore[type-arg]
    """Return the four bitemporal columns shared by all versioned tables."""
    return [
        Column("valid_from", Date, nullable=False),
        Column("valid_to", Date, nullable=True),
        Column(
            "recorded_at",
            DateTime(timezone=True),
            nullable=False,
        ),
        Column(
            "superseded_at",
            DateTime(timezone=True),
            nullable=True,
        ),
    ]


# ---------------------------------------------------------------------------
# Primary bitemporal tables
# ---------------------------------------------------------------------------

measures = Table(
    "measures",
    metadata,
    Column("version_id", BigInteger, primary_key=True, autoincrement=True),
    Column("sid", Integer, nullable=False),
    Column("measure_type_id", String(6), nullable=False),
    Column("goods_nomenclature_code", String(10), nullable=True),
    Column("geographical_area_id", String(4), nullable=False),
    Column("additional_code_type", String(1), nullable=True),
    Column("additional_code_id", String(3), nullable=True),
    Column("quota_order_number", String(6), nullable=True),
    Column("regulation_id", String(8), nullable=False),
    Column("regulation_role", String(1), nullable=False),
    Column("regulation_celex_id", String(20), nullable=True),
    Column("regulation_eli_uri", Text, nullable=True),
    Column("justification_regulation_id", String(8), nullable=True),
    Column("justification_regulation_role", String(1), nullable=True),
    Column("stopped", Boolean, nullable=False, default=False),
    *_bitemporal_columns(),
)

goods_nomenclatures = Table(
    "goods_nomenclatures",
    metadata,
    Column("version_id", BigInteger, primary_key=True, autoincrement=True),
    Column("sid", Integer, nullable=False),
    Column("goods_nomenclature_code", String(10), nullable=False),
    Column("product_line_suffix", String(2), nullable=False),
    Column("indent_number", Integer, nullable=False),
    Column("description", Text, nullable=False),
    Column("statistical_indicator", Boolean, nullable=False, default=False),
    *_bitemporal_columns(),
)

geographical_areas = Table(
    "geographical_areas",
    metadata,
    Column("version_id", BigInteger, primary_key=True, autoincrement=True),
    Column("sid", Integer, nullable=False),
    Column("geographical_area_id", String(4), nullable=False),
    Column("kind", String(10), nullable=False),
    Column("description", Text, nullable=False),
    Column("parent_group_sid", Integer, nullable=True),
    *_bitemporal_columns(),
)

duty_expressions = Table(
    "duty_expressions",
    metadata,
    Column("version_id", BigInteger, primary_key=True, autoincrement=True),
    Column("duty_expression_id", String(2), nullable=False),
    Column("description", Text, nullable=False),
    Column("kind", String(20), nullable=False),
    Column("duty_amount_applicable", Boolean, nullable=False, default=True),
    Column("measurement_unit_applicable", Boolean, nullable=False, default=False),
    Column("monetary_unit_applicable", Boolean, nullable=False, default=False),
    *_bitemporal_columns(),
)

measure_types = Table(
    "measure_types",
    metadata,
    Column("version_id", BigInteger, primary_key=True, autoincrement=True),
    Column("measure_type_id", String(6), nullable=False),
    Column("description", Text, nullable=False),
    Column("trade_movement_code", String(10), nullable=False),
    *_bitemporal_columns(),
)

footnotes = Table(
    "footnotes",
    metadata,
    Column("version_id", BigInteger, primary_key=True, autoincrement=True),
    Column("footnote_type", String(3), nullable=False),
    Column("footnote_id", String(5), nullable=False),
    Column("description", Text, nullable=False),
    *_bitemporal_columns(),
)

# ---------------------------------------------------------------------------
# Child tables (versioned with their parent measure)
# ---------------------------------------------------------------------------

measure_components = Table(
    "measure_components",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column(
        "measure_version_id",
        BigInteger,
        ForeignKey("measures.version_id"),
        nullable=False,
    ),
    Column("duty_expression_id", String(2), nullable=False),
    Column("duty_amount", Numeric, nullable=True),
    Column("monetary_unit_code", String(3), nullable=True),
    Column("measurement_unit_code", String(3), nullable=True),
    Column("measurement_unit_qualifier_code", String(1), nullable=True),
)

measure_conditions = Table(
    "measure_conditions",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column(
        "measure_version_id",
        BigInteger,
        ForeignKey("measures.version_id"),
        nullable=False,
    ),
    Column("sid", Integer, nullable=False),
    Column("condition_code", String(2), nullable=False),
    Column("sequence_number", Integer, nullable=False),
    Column("duty_amount", Numeric, nullable=True),
    Column("monetary_unit_code", String(3), nullable=True),
    Column("measurement_unit_code", String(3), nullable=True),
    Column("measurement_unit_qualifier_code", String(1), nullable=True),
    Column("action_code", String(3), nullable=True),
    Column("certificate_type", String(1), nullable=True),
    Column("certificate_code", String(3), nullable=True),
)

measure_condition_components = Table(
    "measure_condition_components",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column(
        "measure_condition_id",
        BigInteger,
        ForeignKey("measure_conditions.id"),
        nullable=False,
    ),
    Column("duty_expression_id", String(2), nullable=False),
    Column("duty_amount", Numeric, nullable=True),
    Column("monetary_unit_code", String(3), nullable=True),
    Column("measurement_unit_code", String(3), nullable=True),
    Column("measurement_unit_qualifier_code", String(1), nullable=True),
)

measure_footnotes = Table(
    "measure_footnotes",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column(
        "measure_version_id",
        BigInteger,
        ForeignKey("measures.version_id"),
        nullable=False,
    ),
    Column("footnote_type", String(3), nullable=False),
    Column("footnote_id", String(5), nullable=False),
)

measure_excluded_areas = Table(
    "measure_excluded_areas",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column(
        "measure_version_id",
        BigInteger,
        ForeignKey("measures.version_id"),
        nullable=False,
    ),
    Column("geographical_area_id", String(4), nullable=False),
)

# ---------------------------------------------------------------------------
# Indexes for temporal query patterns
# ---------------------------------------------------------------------------

# "Current version of entity X" (most common query)
Index("ix_measures_sid_current", measures.c.sid, measures.c.superseded_at)
Index(
    "ix_goods_nomenclatures_sid_current",
    goods_nomenclatures.c.sid,
    goods_nomenclatures.c.superseded_at,
)
Index(
    "ix_geographical_areas_sid_current",
    geographical_areas.c.sid,
    geographical_areas.c.superseded_at,
)

# "As of legal date D, as known on date E" (full bitemporal query)
Index(
    "ix_measures_bitemporal",
    measures.c.sid,
    measures.c.valid_from,
    measures.c.valid_to,
    measures.c.recorded_at,
    measures.c.superseded_at,
)
Index(
    "ix_goods_nomenclatures_bitemporal",
    goods_nomenclatures.c.sid,
    goods_nomenclatures.c.valid_from,
    goods_nomenclatures.c.valid_to,
    goods_nomenclatures.c.recorded_at,
    goods_nomenclatures.c.superseded_at,
)

# Child table lookups by parent version
Index(
    "ix_measure_components_version",
    measure_components.c.measure_version_id,
)
Index(
    "ix_measure_conditions_version",
    measure_conditions.c.measure_version_id,
)
Index(
    "ix_measure_footnotes_version",
    measure_footnotes.c.measure_version_id,
)
Index(
    "ix_measure_excluded_areas_version",
    measure_excluded_areas.c.measure_version_id,
)

# Goods nomenclature code lookup
Index(
    "ix_measures_goods_code",
    measures.c.goods_nomenclature_code,
)

# All bitemporal tables for convenient iteration
BITEMPORAL_TABLES = (
    measures,
    goods_nomenclatures,
    geographical_areas,
    duty_expressions,
    measure_types,
    footnotes,
)
"""Tables that carry the four bitemporal columns."""
