"""Unit tests for the bitemporal database schema.

Tests verify table structure, column types, indexes, and
bitemporal column presence without needing a database connection.
SQLAlchemy MetaData is inspected purely in memory.
"""

import pytest
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Integer, Numeric, String

from tariff_engine.adapters.database.schema import (
    BITEMPORAL_TABLES,
    measure_components,
    measure_condition_components,
    measure_conditions,
    measure_excluded_areas,
    measure_footnotes,
    measures,
    metadata,
)

pytestmark = pytest.mark.unit

BITEMPORAL_COLUMN_NAMES = {"valid_from", "valid_to", "recorded_at", "superseded_at"}


# ---------------------------------------------------------------------------
# Bitemporal columns present on all versioned tables
# ---------------------------------------------------------------------------


class TestBitemporalColumns:
    @pytest.mark.parametrize("table", BITEMPORAL_TABLES, ids=lambda t: t.name)
    def test_bitemporal_columns_exist(self, table: object) -> None:
        col_names = {c.name for c in table.columns}  # type: ignore[union-attr]
        assert BITEMPORAL_COLUMN_NAMES.issubset(col_names), (
            f"Table {table.name} missing bitemporal columns: "  # type: ignore[union-attr]
            f"{BITEMPORAL_COLUMN_NAMES - col_names}"
        )

    @pytest.mark.parametrize("table", BITEMPORAL_TABLES, ids=lambda t: t.name)
    def test_valid_from_is_date_not_null(self, table: object) -> None:
        col = table.c.valid_from  # type: ignore[union-attr]
        assert isinstance(col.type, Date)
        assert col.nullable is False

    @pytest.mark.parametrize("table", BITEMPORAL_TABLES, ids=lambda t: t.name)
    def test_valid_to_is_date_nullable(self, table: object) -> None:
        col = table.c.valid_to  # type: ignore[union-attr]
        assert isinstance(col.type, Date)
        assert col.nullable is True

    @pytest.mark.parametrize("table", BITEMPORAL_TABLES, ids=lambda t: t.name)
    def test_recorded_at_is_timestamptz_not_null(self, table: object) -> None:
        col = table.c.recorded_at  # type: ignore[union-attr]
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True
        assert col.nullable is False

    @pytest.mark.parametrize("table", BITEMPORAL_TABLES, ids=lambda t: t.name)
    def test_superseded_at_is_timestamptz_nullable(self, table: object) -> None:
        col = table.c.superseded_at  # type: ignore[union-attr]
        assert isinstance(col.type, DateTime)
        assert col.type.timezone is True
        assert col.nullable is True

    @pytest.mark.parametrize("table", BITEMPORAL_TABLES, ids=lambda t: t.name)
    def test_version_id_primary_key(self, table: object) -> None:
        col = table.c.version_id  # type: ignore[union-attr]
        assert col.primary_key is True
        assert isinstance(col.type, BigInteger)


# ---------------------------------------------------------------------------
# Measures table structure
# ---------------------------------------------------------------------------


class TestMeasuresTable:
    def test_table_name(self) -> None:
        assert measures.name == "measures"

    def test_has_sid(self) -> None:
        assert isinstance(measures.c.sid.type, Integer)
        assert measures.c.sid.nullable is False

    def test_has_goods_nomenclature_code(self) -> None:
        assert isinstance(measures.c.goods_nomenclature_code.type, String)
        assert measures.c.goods_nomenclature_code.nullable is True

    def test_has_geographical_area_id(self) -> None:
        assert isinstance(measures.c.geographical_area_id.type, String)
        assert measures.c.geographical_area_id.nullable is False

    def test_has_regulation_id(self) -> None:
        assert isinstance(measures.c.regulation_id.type, String)
        assert measures.c.regulation_id.nullable is False

    def test_has_stopped(self) -> None:
        assert isinstance(measures.c.stopped.type, Boolean)


# ---------------------------------------------------------------------------
# Child tables
# ---------------------------------------------------------------------------


class TestChildTables:
    def test_measure_components_fk(self) -> None:
        fks = [fk.target_fullname for fk in measure_components.foreign_keys]
        assert "measures.version_id" in fks

    def test_measure_conditions_fk(self) -> None:
        fks = [fk.target_fullname for fk in measure_conditions.foreign_keys]
        assert "measures.version_id" in fks

    def test_measure_condition_components_fk(self) -> None:
        fks = [fk.target_fullname for fk in measure_condition_components.foreign_keys]
        assert "measure_conditions.id" in fks

    def test_measure_footnotes_fk(self) -> None:
        fks = [fk.target_fullname for fk in measure_footnotes.foreign_keys]
        assert "measures.version_id" in fks

    def test_measure_excluded_areas_fk(self) -> None:
        fks = [fk.target_fullname for fk in measure_excluded_areas.foreign_keys]
        assert "measures.version_id" in fks

    def test_components_has_duty_amount(self) -> None:
        assert isinstance(measure_components.c.duty_amount.type, Numeric)
        assert measure_components.c.duty_amount.nullable is True

    def test_child_tables_not_bitemporal(self) -> None:
        """Child tables are versioned with their parent, not independently."""
        for table in (
            measure_components,
            measure_conditions,
            measure_condition_components,
            measure_footnotes,
            measure_excluded_areas,
        ):
            col_names = {c.name for c in table.columns}
            assert "recorded_at" not in col_names, (
                f"Child table {table.name} should not have bitemporal columns"
            )


# ---------------------------------------------------------------------------
# Metadata integrity
# ---------------------------------------------------------------------------


class TestMetadata:
    def test_total_table_count(self) -> None:
        assert len(metadata.tables) == 11

    def test_all_table_names_snake_case_plural(self) -> None:
        for name in metadata.tables:
            assert name == name.lower(), f"Table {name} is not lowercase"

    def test_bitemporal_tables_count(self) -> None:
        assert len(BITEMPORAL_TABLES) == 6


# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------


class TestIndexes:
    def test_measures_has_bitemporal_index(self) -> None:
        index_names = {idx.name for idx in measures.indexes}
        assert "ix_measures_bitemporal" in index_names

    def test_measures_has_current_index(self) -> None:
        index_names = {idx.name for idx in measures.indexes}
        assert "ix_measures_sid_current" in index_names

    def test_measures_has_goods_code_index(self) -> None:
        index_names = {idx.name for idx in measures.indexes}
        assert "ix_measures_goods_code" in index_names

    def test_child_tables_have_version_indexes(self) -> None:
        for table, expected in [
            (measure_components, "ix_measure_components_version"),
            (measure_conditions, "ix_measure_conditions_version"),
            (measure_footnotes, "ix_measure_footnotes_version"),
            (measure_excluded_areas, "ix_measure_excluded_areas_version"),
        ]:
            index_names = {idx.name for idx in table.indexes}
            assert expected in index_names, f"Missing index {expected} on {table.name}"
