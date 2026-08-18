"""Unit tests for domain models.

Tests cover:
- Model creation with valid data
- Frozen (immutable) enforcement
- Extra field rejection
- Decimal usage for monetary values
- ValidityPeriod containment and overlap logic
- GoodsNomenclatureCode validation
- DutyExpressionKind includes 2026 regime types
- Measure construction with all components
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError

from tariff_engine.domain.models import (
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
    MeasureType,
    RegulationRole,
    TradeMovementCode,
    ValidityPeriod,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def open_validity() -> ValidityPeriod:
    """A validity period with no end date (still in force)."""
    return ValidityPeriod(valid_from=date(2024, 1, 1))


@pytest.fixture
def closed_validity() -> ValidityPeriod:
    """A validity period with both start and end dates."""
    return ValidityPeriod(valid_from=date(2024, 1, 1), valid_to=date(2024, 12, 31))


@pytest.fixture
def sample_regulation() -> LegalActReference:
    """A sample regulation reference."""
    return LegalActReference(
        regulation_id="R1501880",
        regulation_role=RegulationRole.BASE,
        celex_id="32015R1880",
        official_journal_id="L 274",
        journal_page="10",
        date_published=date(2015, 10, 20),
        description="Council Regulation on agricultural products",
    )


# ---------------------------------------------------------------------------
# ValidityPeriod
# ---------------------------------------------------------------------------


class TestValidityPeriod:
    def test_open_ended_period(self, open_validity: ValidityPeriod) -> None:
        assert open_validity.valid_from == date(2024, 1, 1)
        assert open_validity.valid_to is None

    def test_closed_period(self, closed_validity: ValidityPeriod) -> None:
        assert closed_validity.valid_to == date(2024, 12, 31)

    def test_valid_to_before_valid_from_rejected(self) -> None:
        with pytest.raises(PydanticValidationError):
            ValidityPeriod(
                valid_from=date(2024, 6, 1),
                valid_to=date(2024, 1, 1),
            )

    def test_same_day_validity_allowed(self) -> None:
        vp = ValidityPeriod(
            valid_from=date(2024, 6, 1),
            valid_to=date(2024, 6, 1),
        )
        assert vp.valid_from == vp.valid_to

    def test_contains_date_inside(self, closed_validity: ValidityPeriod) -> None:
        assert closed_validity.contains(date(2024, 6, 15)) is True

    def test_contains_date_on_start(self, closed_validity: ValidityPeriod) -> None:
        assert closed_validity.contains(date(2024, 1, 1)) is True

    def test_contains_date_on_end_excluded(self, closed_validity: ValidityPeriod) -> None:
        """valid_to is exclusive in the half-open interval."""
        assert closed_validity.contains(date(2024, 12, 31)) is False

    def test_contains_date_before_start(self, closed_validity: ValidityPeriod) -> None:
        assert closed_validity.contains(date(2023, 12, 31)) is False

    def test_contains_open_ended(self, open_validity: ValidityPeriod) -> None:
        assert open_validity.contains(date(2099, 12, 31)) is True

    def test_overlaps_true(self) -> None:
        a = ValidityPeriod(valid_from=date(2024, 1, 1), valid_to=date(2024, 6, 30))
        b = ValidityPeriod(valid_from=date(2024, 3, 1), valid_to=date(2024, 9, 30))
        assert a.overlaps(b) is True
        assert b.overlaps(a) is True

    def test_overlaps_false_adjacent(self) -> None:
        a = ValidityPeriod(valid_from=date(2024, 1, 1), valid_to=date(2024, 6, 1))
        b = ValidityPeriod(valid_from=date(2024, 6, 1), valid_to=date(2024, 12, 31))
        assert a.overlaps(b) is False

    def test_overlaps_open_ended(self) -> None:
        a = ValidityPeriod(valid_from=date(2024, 1, 1))
        b = ValidityPeriod(valid_from=date(2024, 6, 1), valid_to=date(2024, 12, 31))
        assert a.overlaps(b) is True


# ---------------------------------------------------------------------------
# GoodsNomenclatureCode
# ---------------------------------------------------------------------------


class TestGoodsNomenclatureCode:
    def test_valid_code(self) -> None:
        gnc = GoodsNomenclatureCode(code="0201300020")
        assert gnc.hs_heading == "0201"
        assert gnc.hs_code == "020130"
        assert gnc.cn_code == "02013000"
        assert gnc.taric_code == "0201300020"

    def test_too_short_rejected(self) -> None:
        with pytest.raises(PydanticValidationError):
            GoodsNomenclatureCode(code="020130")

    def test_too_long_rejected(self) -> None:
        with pytest.raises(PydanticValidationError):
            GoodsNomenclatureCode(code="02013000201")

    def test_non_digit_rejected(self) -> None:
        with pytest.raises(PydanticValidationError):
            GoodsNomenclatureCode(code="020130AB20")

    def test_str_representation(self) -> None:
        gnc = GoodsNomenclatureCode(code="0201300020")
        assert str(gnc) == "0201300020"


# ---------------------------------------------------------------------------
# Model immutability and strictness
# ---------------------------------------------------------------------------


class TestModelConstraints:
    def test_frozen_rejects_mutation(self, open_validity: ValidityPeriod) -> None:
        with pytest.raises(PydanticValidationError):
            open_validity.valid_from = date(2025, 1, 1)  # type: ignore[misc]

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(PydanticValidationError):
            ValidityPeriod(
                valid_from=date(2024, 1, 1),
                surprise_field="should fail",  # type: ignore[call-arg]
            )


# ---------------------------------------------------------------------------
# DutyExpressionKind (2026 regime coverage)
# ---------------------------------------------------------------------------


class TestDutyExpressionKind:
    def test_flat_per_item_exists(self) -> None:
        assert DutyExpressionKind.FLAT_PER_ITEM.value == "flat_per_item"

    def test_handling_fee_exists(self) -> None:
        assert DutyExpressionKind.HANDLING_FEE.value == "handling_fee"

    def test_standard_types_exist(self) -> None:
        assert DutyExpressionKind.AD_VALOREM.value == "ad_valorem"
        assert DutyExpressionKind.SPECIFIC.value == "specific"
        assert DutyExpressionKind.COMPOUND.value == "compound"


# ---------------------------------------------------------------------------
# MeasureComponent with Decimal
# ---------------------------------------------------------------------------


class TestMeasureComponent:
    def test_decimal_duty_amount(self) -> None:
        mc = MeasureComponent(
            duty_expression_id="01",
            duty_amount=Decimal("128.7"),
            monetary_unit_code="EUR",
            measurement_unit_code="DTN",
        )
        assert mc.duty_amount == Decimal("128.7")
        assert isinstance(mc.duty_amount, Decimal)

    def test_component_without_amount(self) -> None:
        mc = MeasureComponent(duty_expression_id="01")
        assert mc.duty_amount is None
        assert mc.monetary_unit_code is None

    def test_flat_per_item_eur3(self) -> None:
        """EUR 3 flat duty per item for the 2026 low value regime."""
        mc = MeasureComponent(
            duty_expression_id="01",
            duty_amount=Decimal("3"),
            monetary_unit_code="EUR",
            measurement_unit_code="NAR",
        )
        assert mc.duty_amount == Decimal("3")
        assert mc.monetary_unit_code == "EUR"
        assert mc.measurement_unit_code == "NAR"


# ---------------------------------------------------------------------------
# Full Measure assembly
# ---------------------------------------------------------------------------


class TestMeasure:
    def test_minimal_measure(self, sample_regulation: LegalActReference) -> None:
        m = Measure(
            sid=1234567,
            measure_type_id="103",
            geographical_area_id="1011",
            validity=ValidityPeriod(valid_from=date(2024, 1, 1)),
            regulation=sample_regulation,
        )
        assert m.sid == 1234567
        assert m.measure_type_id == "103"
        assert m.components == ()
        assert m.conditions == ()
        assert m.stopped is False

    def test_measure_with_components(self, sample_regulation: LegalActReference) -> None:
        component = MeasureComponent(
            duty_expression_id="01",
            duty_amount=Decimal("22"),
        )
        m = Measure(
            sid=1234568,
            measure_type_id="103",
            goods_nomenclature_code=GoodsNomenclatureCode(code="0302320000"),
            geographical_area_id="1011",
            validity=ValidityPeriod(valid_from=date(2024, 1, 1)),
            regulation=sample_regulation,
            components=(component,),
        )
        assert len(m.components) == 1
        assert m.components[0].duty_amount == Decimal("22")

    def test_measure_with_excluded_areas(self, sample_regulation: LegalActReference) -> None:
        m = Measure(
            sid=1234569,
            measure_type_id="490",
            geographical_area_id="1011",
            validity=ValidityPeriod(valid_from=date(2024, 1, 1)),
            regulation=sample_regulation,
            excluded_geographical_areas=("TR", "MA"),
        )
        assert "TR" in m.excluded_geographical_areas
        assert "MA" in m.excluded_geographical_areas

    def test_measure_with_condition(self, sample_regulation: LegalActReference) -> None:
        condition = MeasureCondition(
            sid=997085,
            condition_code="Y",
            sequence_number=3,
            action_code="09",
        )
        m = Measure(
            sid=1234570,
            measure_type_id="710",
            geographical_area_id="1011",
            validity=ValidityPeriod(
                valid_from=date(2024, 12, 20),
                valid_to=date(2025, 6, 30),
            ),
            regulation=sample_regulation,
            conditions=(condition,),
        )
        assert len(m.conditions) == 1
        assert m.conditions[0].condition_code == "Y"

    def test_measure_with_footnote(self, sample_regulation: LegalActReference) -> None:
        footnote = Footnote(
            footnote_type="CD",
            footnote_id="370",
            description="Required documentation for import",
            validity=ValidityPeriod(valid_from=date(2024, 1, 1)),
        )
        m = Measure(
            sid=1234571,
            measure_type_id="103",
            geographical_area_id="1011",
            validity=ValidityPeriod(valid_from=date(2024, 1, 1)),
            regulation=sample_regulation,
            footnotes=(footnote,),
        )
        assert len(m.footnotes) == 1


# ---------------------------------------------------------------------------
# LegalActReference
# ---------------------------------------------------------------------------


class TestLegalActReference:
    def test_minimal_reference(self) -> None:
        ref = LegalActReference(
            regulation_id="R9514840",
            regulation_role=RegulationRole.BASE,
        )
        assert ref.regulation_id == "R9514840"
        assert ref.celex_id is None

    def test_full_reference(self) -> None:
        ref = LegalActReference(
            regulation_id="R1501880",
            regulation_role=RegulationRole.BASE,
            celex_id="32015R1880",
            eli_uri="http://data.europa.eu/eli/reg/2015/1880",
            official_journal_id="L 274",
            journal_page="10",
            date_published=date(2015, 10, 20),
            description="Council Regulation",
        )
        assert ref.celex_id == "32015R1880"
        assert ref.eli_uri is not None


# ---------------------------------------------------------------------------
# GeographicalArea and remaining entities
# ---------------------------------------------------------------------------


class TestGeographicalArea:
    def test_country(self) -> None:
        ga = GeographicalArea(
            sid=111,
            geographical_area_id="DE",
            kind=GeographicalAreaKind.COUNTRY,
            description="Germany",
            validity=ValidityPeriod(valid_from=date(1958, 1, 1)),
        )
        assert ga.kind == GeographicalAreaKind.COUNTRY

    def test_group(self) -> None:
        ga = GeographicalArea(
            sid=400,
            geographical_area_id="1011",
            kind=GeographicalAreaKind.GROUP,
            description="Erga Omnes",
            validity=ValidityPeriod(valid_from=date(1970, 1, 1)),
        )
        assert ga.kind == GeographicalAreaKind.GROUP


class TestGoodsNomenclature:
    def test_creation(self) -> None:
        gn = GoodsNomenclature(
            sid=96157,
            goods_nomenclature_code=GoodsNomenclatureCode(code="0201300020"),
            product_line_suffix="80",
            indent_number=2,
            description="Buffalo meat",
            validity=ValidityPeriod(valid_from=date(2011, 12, 1)),
        )
        assert gn.goods_nomenclature_code.hs_heading == "0201"
        assert gn.indent_number == 2


class TestMeasureType:
    def test_creation(self) -> None:
        mt = MeasureType(
            measure_type_id="103",
            description="Third country duty",
            trade_movement_code=TradeMovementCode.IMPORT,
            validity=ValidityPeriod(valid_from=date(1972, 1, 1)),
        )
        assert mt.measure_type_id == "103"
        assert mt.trade_movement_code == TradeMovementCode.IMPORT
