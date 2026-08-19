"""Worked example tests for the 2026 low value consignment regime.

Proves the EUR 3 flat customs duty and the EUR 2 handling fee
model correctly through the domain and round-trip through
serialization/deserialization.

Legal basis: Council Regulation (EU) 2026/382
Implementation: Commission Implementing Regulation (EU) 2026/1200
"""

from datetime import date
from decimal import Decimal

import pytest

from tariff_engine.domain.errors import ValidationError
from tariff_engine.domain.models import (
    DutyExpression,
    DutyExpressionKind,
    GoodsNomenclatureCode,
    LegalActReference,
    Measure,
    MeasureComponent,
    RegulationRole,
    ValidityPeriod,
)
from tariff_engine.domain.validation import (
    is_customs_duty,
    validate_flat_per_item_component,
    validate_handling_fee_component,
    validate_low_value_consignment_measure,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures: realistic 2026 regime data
# ---------------------------------------------------------------------------

REGULATION_2026_382 = LegalActReference(
    regulation_id="R2600382",
    regulation_role=RegulationRole.BASE,
    celex_id="32026R0382",
    official_journal_id="L 382",
    date_published=date(2026, 4, 30),
    description="Flat rate customs duty on low value consignments",
)

LOW_VALUE_VALIDITY = ValidityPeriod(
    valid_from=date(2026, 7, 1),
    valid_to=date(2028, 7, 1),
)

FLAT_DUTY_EXPRESSION = DutyExpression(
    duty_expression_id="99",
    description="Flat per item customs duty for low value consignments",
    kind=DutyExpressionKind.FLAT_PER_ITEM,
    duty_amount_applicable=True,
    measurement_unit_applicable=False,
    monetary_unit_applicable=True,
    validity=LOW_VALUE_VALIDITY,
)

HANDLING_FEE_EXPRESSION = DutyExpression(
    duty_expression_id="98",
    description="Per parcel handling fee (not a customs duty)",
    kind=DutyExpressionKind.HANDLING_FEE,
    duty_amount_applicable=True,
    measurement_unit_applicable=False,
    monetary_unit_applicable=True,
    validity=ValidityPeriod(
        valid_from=date(2026, 11, 1),
        valid_to=date(2028, 7, 1),
    ),
)


# ---------------------------------------------------------------------------
# DutyExpressionKind.is_customs_duty
# ---------------------------------------------------------------------------


class TestDutyExpressionKindIsCustomsDuty:
    def test_flat_per_item_is_customs_duty(self) -> None:
        assert is_customs_duty(DutyExpressionKind.FLAT_PER_ITEM) is True

    def test_handling_fee_is_not_customs_duty(self) -> None:
        assert is_customs_duty(DutyExpressionKind.HANDLING_FEE) is False

    def test_ad_valorem_is_customs_duty(self) -> None:
        assert is_customs_duty(DutyExpressionKind.AD_VALOREM) is True

    def test_specific_is_customs_duty(self) -> None:
        assert is_customs_duty(DutyExpressionKind.SPECIFIC) is True

    def test_compound_is_customs_duty(self) -> None:
        assert is_customs_duty(DutyExpressionKind.COMPOUND) is True


# ---------------------------------------------------------------------------
# EUR 3 flat duty: worked example
# ---------------------------------------------------------------------------


class TestEur3FlatDuty:
    """Worked example: EUR 3 flat customs duty per tariff subheading.

    Scenario: A consumer in Germany orders a parcel from China
    containing a phone case (HS 3926) and a T-shirt (HS 6109).
    Two different 6-digit subheadings, so EUR 3 x 2 = EUR 6 total.
    """

    def test_single_item_measure(self) -> None:
        """One tariff subheading, one EUR 3 charge."""
        component = MeasureComponent(
            duty_expression_id="99",
            duty_amount=Decimal("3"),
            monetary_unit_code="EUR",
        )
        measure = Measure(
            sid=9900001,
            measure_type_id="LVC",
            goods_nomenclature_code=GoodsNomenclatureCode(code="3926909790"),
            geographical_area_id="1011",
            validity=LOW_VALUE_VALIDITY,
            regulation=REGULATION_2026_382,
            components=(component,),
        )
        assert measure.components[0].duty_amount == Decimal("3")
        assert measure.components[0].monetary_unit_code == "EUR"
        assert measure.validity.valid_from == date(2026, 7, 1)
        assert measure.validity.valid_to == date(2028, 7, 1)

    def test_multi_subheading_parcel(self) -> None:
        """Two different subheadings in one parcel: two separate measures."""
        measures = []
        for code in ("3926909790", "6109100020"):
            component = MeasureComponent(
                duty_expression_id="99",
                duty_amount=Decimal("3"),
                monetary_unit_code="EUR",
            )
            measures.append(
                Measure(
                    sid=9900002 + len(measures),
                    measure_type_id="LVC",
                    goods_nomenclature_code=GoodsNomenclatureCode(code=code),
                    geographical_area_id="1011",
                    validity=LOW_VALUE_VALIDITY,
                    regulation=REGULATION_2026_382,
                    components=(component,),
                )
            )
        total_duty = sum(
            m.components[0].duty_amount for m in measures if m.components[0].duty_amount is not None
        )
        assert total_duty == Decimal("6")
        assert len(measures) == 2

    def test_round_trip_serialization(self) -> None:
        """EUR 3 measure survives model_dump and model_validate."""
        component = MeasureComponent(
            duty_expression_id="99",
            duty_amount=Decimal("3"),
            monetary_unit_code="EUR",
        )
        original = Measure(
            sid=9900010,
            measure_type_id="LVC",
            goods_nomenclature_code=GoodsNomenclatureCode(code="3926909790"),
            geographical_area_id="1011",
            validity=LOW_VALUE_VALIDITY,
            regulation=REGULATION_2026_382,
            components=(component,),
        )
        data = original.model_dump()
        restored = Measure.model_validate(data)
        assert restored == original
        assert restored.components[0].duty_amount == Decimal("3")
        assert isinstance(restored.components[0].duty_amount, Decimal)

    def test_flat_duty_expression_attributes(self) -> None:
        """DutyExpression for FLAT_PER_ITEM has correct applicability."""
        assert FLAT_DUTY_EXPRESSION.kind == DutyExpressionKind.FLAT_PER_ITEM
        assert FLAT_DUTY_EXPRESSION.duty_amount_applicable is True
        assert FLAT_DUTY_EXPRESSION.monetary_unit_applicable is True
        assert FLAT_DUTY_EXPRESSION.measurement_unit_applicable is False


# ---------------------------------------------------------------------------
# EUR 2 handling fee: worked example
# ---------------------------------------------------------------------------


class TestHandlingFee:
    """Worked example: EUR 2 per parcel handling fee.

    The handling fee is NOT a customs duty. It is collected by
    member states under a separate legal basis.
    """

    def test_handling_fee_measure(self) -> None:
        component = MeasureComponent(
            duty_expression_id="98",
            duty_amount=Decimal("2"),
            monetary_unit_code="EUR",
        )
        measure = Measure(
            sid=9900020,
            measure_type_id="HFE",
            geographical_area_id="1011",
            validity=ValidityPeriod(
                valid_from=date(2026, 11, 1),
                valid_to=date(2028, 7, 1),
            ),
            regulation=REGULATION_2026_382,
            components=(component,),
        )
        assert measure.components[0].duty_amount == Decimal("2")
        assert measure.measure_type_id == "HFE"

    def test_handling_fee_is_not_customs_duty(self) -> None:
        assert HANDLING_FEE_EXPRESSION.kind == DutyExpressionKind.HANDLING_FEE
        assert is_customs_duty(HANDLING_FEE_EXPRESSION.kind) is False

    def test_handling_fee_round_trip(self) -> None:
        component = MeasureComponent(
            duty_expression_id="98",
            duty_amount=Decimal("2"),
            monetary_unit_code="EUR",
        )
        original = Measure(
            sid=9900021,
            measure_type_id="HFE",
            geographical_area_id="1011",
            validity=ValidityPeriod(
                valid_from=date(2026, 11, 1),
                valid_to=date(2028, 7, 1),
            ),
            regulation=REGULATION_2026_382,
            components=(component,),
        )
        data = original.model_dump()
        restored = Measure.model_validate(data)
        assert restored == original


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------


class TestFlatPerItemValidation:
    def test_valid_component(self) -> None:
        component = MeasureComponent(
            duty_expression_id="99",
            duty_amount=Decimal("3"),
            monetary_unit_code="EUR",
        )
        validate_flat_per_item_component(component)

    def test_missing_amount_rejected(self) -> None:
        component = MeasureComponent(
            duty_expression_id="99",
            monetary_unit_code="EUR",
        )
        with pytest.raises(ValidationError, match="requires a duty_amount"):
            validate_flat_per_item_component(component)

    def test_zero_amount_rejected(self) -> None:
        component = MeasureComponent(
            duty_expression_id="99",
            duty_amount=Decimal("0"),
            monetary_unit_code="EUR",
        )
        with pytest.raises(ValidationError, match="must be positive"):
            validate_flat_per_item_component(component)

    def test_negative_amount_rejected(self) -> None:
        component = MeasureComponent(
            duty_expression_id="99",
            duty_amount=Decimal("-1"),
            monetary_unit_code="EUR",
        )
        with pytest.raises(ValidationError, match="must be positive"):
            validate_flat_per_item_component(component)

    def test_missing_currency_rejected(self) -> None:
        component = MeasureComponent(
            duty_expression_id="99",
            duty_amount=Decimal("3"),
        )
        with pytest.raises(ValidationError, match="requires a monetary_unit_code"):
            validate_flat_per_item_component(component)

    def test_qualifier_present_rejected(self) -> None:
        component = MeasureComponent(
            duty_expression_id="99",
            duty_amount=Decimal("3"),
            monetary_unit_code="EUR",
            measurement_unit_qualifier_code="A",
        )
        with pytest.raises(
            ValidationError, match="must not have a measurement_unit_qualifier_code"
        ):
            validate_flat_per_item_component(component)


class TestHandlingFeeValidation:
    def test_valid_component(self) -> None:
        component = MeasureComponent(
            duty_expression_id="98",
            duty_amount=Decimal("2"),
            monetary_unit_code="EUR",
        )
        validate_handling_fee_component(component)

    def test_missing_amount_rejected(self) -> None:
        component = MeasureComponent(
            duty_expression_id="98",
            monetary_unit_code="EUR",
        )
        with pytest.raises(ValidationError, match="requires a duty_amount"):
            validate_handling_fee_component(component)

    def test_missing_currency_rejected(self) -> None:
        component = MeasureComponent(
            duty_expression_id="98",
            duty_amount=Decimal("2"),
        )
        with pytest.raises(ValidationError, match="requires a monetary_unit_code"):
            validate_handling_fee_component(component)


class TestLowValueMeasureValidation:
    def test_empty_components_rejected(self) -> None:
        measure = Measure(
            sid=9900099,
            measure_type_id="LVC",
            geographical_area_id="1011",
            validity=LOW_VALUE_VALIDITY,
            regulation=REGULATION_2026_382,
        )
        with pytest.raises(ValidationError, match="must have at least one component"):
            validate_low_value_consignment_measure(measure)

    def test_valid_measure_passes(self) -> None:
        component = MeasureComponent(
            duty_expression_id="99",
            duty_amount=Decimal("3"),
            monetary_unit_code="EUR",
        )
        measure = Measure(
            sid=9900100,
            measure_type_id="LVC",
            goods_nomenclature_code=GoodsNomenclatureCode(code="3926909790"),
            geographical_area_id="1011",
            validity=LOW_VALUE_VALIDITY,
            regulation=REGULATION_2026_382,
            components=(component,),
        )
        validate_low_value_consignment_measure(measure)
