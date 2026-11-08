from dataclasses import dataclass

from mechprox.domain.enums import ValidationSeverity
from mechprox.domain.model import EngineeringModel
from mechprox.domain.units import UnitService
from mechprox.domain.validation_calculations import validate_calculation_records
from mechprox.domain.validation_commercial import validate_commercial_records
from mechprox.domain.validation_context import ValidationContext, ValidationIssue
from mechprox.domain.validation_engineering import (
    validate_engineering_networks,
    validate_engineering_objects,
)
from mechprox.domain.validation_structure import validate_project_structure


@dataclass(frozen=True, slots=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(
            issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR
        )

    def raise_for_errors(self) -> None:
        if self.errors:
            details = "; ".join(
                f"{issue.path}: {issue.message}" for issue in self.errors
            )
            raise ModelValidationError(details)


class ModelValidationError(ValueError):
    pass


class ModelValidator:
    """Coordinates independent validators for the CEDM bounded contexts."""

    def __init__(self, unit_service: UnitService | None = None) -> None:
        self._units = unit_service or UnitService()

    def validate(self, model: EngineeringModel) -> ValidationReport:
        context = ValidationContext(model=model, units=self._units)
        validate_project_structure(context)
        validate_engineering_objects(context)
        validate_engineering_networks(context)
        validate_commercial_records(context)
        validate_calculation_records(context)
        return ValidationReport(tuple(context.issues))
