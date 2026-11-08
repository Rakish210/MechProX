from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

import pint

from mechpro.domain.base import Quantity


class UnitValidationError(ValueError):
    pass


class UnitService:
    """Offline dimensional validation and conversion using Pint's unit definitions.

    Project-specific unit extensions can be supplied as local Pint definition files.
    Engineering design coefficients and code-specific limits do not belong here.
    """

    def __init__(self, definition_files: Sequence[Path] = ()) -> None:
        # Pint's runtime accepts Decimal here; its current type stub restricts this to float.
        self._registry = pint.UnitRegistry(non_int_type=Decimal)  # pyright: ignore[reportArgumentType]
        for definition_file in definition_files:
            self._registry.load_definitions(str(definition_file))

    def validate(
        self,
        quantity: Quantity,
        *,
        expected_dimension: str | None = None,
    ) -> None:
        try:
            measured = self._registry.Quantity(quantity.value, quantity.unit_code)
        except (pint.errors.UndefinedUnitError, TypeError, ValueError) as exc:
            raise UnitValidationError(
                f"Unknown or invalid unit '{quantity.unit_code}'."
            ) from exc

        if expected_dimension is not None and not measured.check(expected_dimension):
            raise UnitValidationError(
                f"Unit '{quantity.unit_code}' has dimensionality "
                f"'{measured.dimensionality}', expected '{expected_dimension}'."
            )

    def convert(self, quantity: Quantity, target_unit: str) -> Quantity:
        self.validate(quantity)
        try:
            converted = self._registry.Quantity(
                quantity.value, quantity.unit_code
            ).to(target_unit)
        except (pint.errors.UndefinedUnitError, pint.errors.DimensionalityError) as exc:
            raise UnitValidationError(
                f"Cannot convert '{quantity.unit_code}' to '{target_unit}'."
            ) from exc
        return Quantity(
            value=Decimal(str(converted.magnitude)),
            unit_code=target_unit,
        )

    def are_compatible(self, first_unit: str, second_unit: str) -> bool:
        try:
            self._registry.Quantity(Decimal(1), first_unit).to(second_unit)
        except (pint.errors.UndefinedUnitError, pint.errors.DimensionalityError):
            return False
        return True
