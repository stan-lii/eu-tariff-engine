"""Domain validation rules for duty expressions and measures.

Pure functions. No I/O, no database, no network.
These enforce structural consistency that goes beyond what
Pydantic field constraints alone can express.
"""

from decimal import Decimal

from tariff_engine.domain.errors import ValidationError
from tariff_engine.domain.models import (
    DutyExpressionKind,
    Measure,
    MeasureComponent,
)


def is_customs_duty(kind: DutyExpressionKind) -> bool:
    """Return True if this expression kind represents a customs duty.

    HANDLING_FEE is explicitly not a customs duty. It is a separate
    per-parcel fee collected by member states under the 2026 low
    value consignment regime.
    """
    return kind is not DutyExpressionKind.HANDLING_FEE


def validate_flat_per_item_component(component: MeasureComponent) -> None:
    """Validate that a FLAT_PER_ITEM component has the required structure.

    Rules:
    - duty_amount must be present and positive
    - monetary_unit_code must be present
    - measurement_unit_qualifier_code must be absent

    Raises:
        ValidationError: if any rule is violated
    """
    if component.duty_amount is None:
        raise ValidationError("FLAT_PER_ITEM component requires a duty_amount")

    if component.duty_amount <= Decimal("0"):
        raise ValidationError(
            f"FLAT_PER_ITEM duty_amount must be positive, got {component.duty_amount}"
        )

    if component.monetary_unit_code is None:
        raise ValidationError("FLAT_PER_ITEM component requires a monetary_unit_code")

    if component.measurement_unit_qualifier_code is not None:
        raise ValidationError(
            "FLAT_PER_ITEM component must not have a measurement_unit_qualifier_code"
        )


def validate_handling_fee_component(component: MeasureComponent) -> None:
    """Validate that a HANDLING_FEE component has the required structure.

    Rules:
    - duty_amount must be present and positive
    - monetary_unit_code must be present

    Raises:
        ValidationError: if any rule is violated
    """
    if component.duty_amount is None:
        raise ValidationError("HANDLING_FEE component requires a duty_amount")

    if component.duty_amount <= Decimal("0"):
        raise ValidationError(
            f"HANDLING_FEE duty_amount must be positive, got {component.duty_amount}"
        )

    if component.monetary_unit_code is None:
        raise ValidationError("HANDLING_FEE component requires a monetary_unit_code")


def validate_low_value_consignment_measure(measure: Measure) -> None:
    """Validate that a low value consignment measure is structurally consistent.

    A low value consignment measure must have at least one component.
    Each component is validated according to its duty expression kind,
    which must be determined by the caller based on the DutyExpression
    registry.

    Raises:
        ValidationError: if the measure has no components
    """
    if not measure.components:
        raise ValidationError("Low value consignment measure must have at least one component")


DUTY_EXPRESSION_VALIDATORS = {
    DutyExpressionKind.FLAT_PER_ITEM: validate_flat_per_item_component,
    DutyExpressionKind.HANDLING_FEE: validate_handling_fee_component,
}
"""Registry mapping duty expression kinds to their component validators."""
