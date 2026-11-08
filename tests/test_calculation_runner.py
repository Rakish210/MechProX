from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mechprox.calculations import (
    CalculationContext,
    CalculationEngineRegistry,
    CalculationOutput,
    CalculationRequest,
    CalculationResultDraft,
    CalculationRunner,
)
from mechprox.calculations.runner import CalculationPreconditionError
from mechprox.data import models  # noqa: F401
from mechprox.data.db import Base
from mechprox.data.parameter_registry_repository import ParameterRegistryRepository
from mechprox.data.project_repository import CalculationAppendError, ProjectRepository
from mechprox.domain.base import Quantity, QuantityValue, ScalarValue
from mechprox.domain.engineering import LinearElement
from mechprox.domain.enums import (
    CalculationPurpose,
    CalculationState,
    InformationOrigin,
)
from mechprox.domain.example import create_natural_gas_reference_model
from mechprox.domain.model import EngineeringModel
from mechprox.domain.parameters import (
    ParameterDefinition,
    ParameterRevision,
    ParameterRevisionStatus,
    ParameterValueKind,
)
from mechprox.domain.validation import ModelValidator


class TotalLengthTestEngine:
    method_code = "TEST.PIPE_LENGTH"
    method_revision = "1"
    engine_name = "test-engine"
    engine_version = "1.0"
    required_parameter_codes = ("TEST.LENGTH_FACTOR",)

    def calculate(self, context: CalculationContext) -> CalculationOutput:
        factor = context.parameters["TEST.LENGTH_FACTOR"].value
        if not isinstance(factor, ScalarValue) or not isinstance(factor.value, Decimal):
            raise TypeError("Test engine expects a Decimal scalar parameter.")
        total_length = sum(
            (
                item.length.value
                for item in context.input_objects
                if isinstance(item, LinearElement)
            ),
            Decimal(0),
        )
        result_value = QuantityValue(
            quantity=Quantity(
                value=total_length * factor.value,
                unit_code="meter",
            )
        )
        return CalculationOutput(
            results=(
                CalculationResultDraft(
                    result_code="test.total_scaled_length",
                    label="Scaled total length",
                    value=result_value,
                    source_object_ids=tuple(item.id for item in context.input_objects),
                    source_parameter_codes=("TEST.LENGTH_FACTOR",),
                ),
            )
        )


class FailingTestEngine(TotalLengthTestEngine):
    method_code = "TEST.FAILING"

    def calculate(self, context: CalculationContext) -> CalculationOutput:
        raise RuntimeError("deliberate test failure")


@pytest.fixture
def repositories(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'calculation.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return ProjectRepository(factory), ParameterRegistryRepository(factory)


@pytest.fixture
def model_and_runner(repositories):
    project_repository, parameter_repository = repositories
    model = create_natural_gas_reference_model()
    project_repository.create(model)

    definition = ParameterDefinition(
        code="TEST.LENGTH_FACTOR",
        name="Test length factor",
        discipline_code="GENERAL",
        category_code="TEST",
        value_kind=ParameterValueKind.SCALAR,
    )
    parameter_repository.register_definition(definition)
    parameter_repository.add_revision(
        ParameterRevision(
            definition_id=definition.id,
            revision_code="A",
            value=ScalarValue(value=Decimal(2)),
            status=ParameterRevisionStatus.APPROVED,
            origin=InformationOrigin.USER_INPUT,
            created_by="test",
            approved_by="test",
        )
    )

    registry = CalculationEngineRegistry()
    registry.register(TotalLengthTestEngine())
    registry.register(FailingTestEngine())
    runner = CalculationRunner(registry, parameter_repository)
    return model, project_repository, runner


def _request(
    model: EngineeringModel,
    method_code: str = "TEST.PIPE_LENGTH",
) -> CalculationRequest:
    return CalculationRequest(
        project_id=model.project.id,
        method_code=method_code,
        method_revision="1",
        input_object_ids=tuple(
            item.id for item in model.objects if isinstance(item, LinearElement)
        ),
        parameter_codes=("TEST.LENGTH_FACTOR",),
        effective_date=date(2026, 11, 8),
        purpose=CalculationPurpose.ENGINEERING,
    )


def test_runner_creates_reproducible_run_and_persists_results(model_and_runner) -> None:
    model, project_repository, runner = model_and_runner

    execution = runner.run_and_save(model, _request(model), project_repository)
    restored = project_repository.get(model.project.id)

    assert execution.run.state == CalculationState.COMPLETED
    assert execution.run.input_hash
    assert execution.run.output_hash
    assert len(execution.run.input_snapshots) == 3
    assert all(item.object_snapshot is not None for item in execution.run.input_snapshots)
    assert all(
        parameter.revision_snapshot is not None
        for item in execution.run.input_snapshots
        for parameter in item.parameter_snapshots
    )
    assert len(execution.results) == 1
    assert isinstance(execution.results[0].value, QuantityValue)
    assert execution.results[0].value.quantity.value == Decimal("26.0")
    assert restored.calculation_runs[-1] == execution.run
    assert restored.calculation_results[-1] == execution.results[0]
    assert ModelValidator().validate(restored).is_valid

    original_pipe = next(
        item for item in restored.objects if isinstance(item, LinearElement)
    )
    revised_pipe = original_pipe.model_copy(
        update={"length": Quantity(value=Decimal(99), unit_code="meter")}
    )
    revised_objects = tuple(
        revised_pipe if item.id == original_pipe.id else item
        for item in restored.objects
    )
    project_repository.save(restored.model_copy(update={"objects": revised_objects}))
    historical = project_repository.get(model.project.id).calculation_runs[-1]
    historical_pipe = historical.input_snapshots[0].object_snapshot
    assert isinstance(historical_pipe, LinearElement)
    assert historical_pipe.length.value == Decimal("6.0")


def test_runner_records_engine_failure(model_and_runner) -> None:
    model, project_repository, runner = model_and_runner

    execution = runner.run_and_save(
        model,
        _request(model, method_code="TEST.FAILING"),
        project_repository,
    )

    assert execution.run.state == CalculationState.FAILED
    assert execution.run.error_message is not None
    assert "deliberate test failure" in execution.run.error_message
    assert execution.results == ()
    assert project_repository.get(model.project.id).calculation_runs[-1] == execution.run


def test_runner_rejects_missing_controlled_object_revision(model_and_runner) -> None:
    model, _, runner = model_and_runner
    first_pipe = next(item for item in model.objects if isinstance(item, LinearElement))
    invalid_pipe = first_pipe.model_copy(update={"revision_id": None})
    invalid_objects = tuple(
        invalid_pipe if item.id == first_pipe.id else item for item in model.objects
    )
    invalid_model = model.model_copy(update={"objects": invalid_objects})

    with pytest.raises(CalculationPreconditionError, match="no controlled revision"):
        runner.run(invalid_model, _request(invalid_model))


def test_runner_rejects_unrequested_parameter_dependency(model_and_runner) -> None:
    model, _, runner = model_and_runner
    request = _request(model)
    invalid_request = CalculationRequest(
        project_id=request.project_id,
        method_code=request.method_code,
        method_revision=request.method_revision,
        input_object_ids=request.input_object_ids,
        parameter_codes=(),
        effective_date=request.effective_date,
    )

    with pytest.raises(CalculationPreconditionError, match="Required calculation parameters"):
        runner.run(model, invalid_request)


def test_runner_rejects_result_referencing_uncaptured_objects(model_and_runner) -> None:
    model, _, runner = model_and_runner

    class InvalidResultEngine(TotalLengthTestEngine):
        method_code = "TEST.INVALID_RESULT"

        def calculate(self, context: CalculationContext) -> CalculationOutput:
            output = super().calculate(context)
            invalid = output.results[0]
            return CalculationOutput(
                results=(
                    CalculationResultDraft(
                        result_code=invalid.result_code,
                        label=invalid.label,
                        value=invalid.value,
                        source_object_ids=(model.project.id,),
                        source_parameter_codes=invalid.source_parameter_codes,
                    ),
                )
            )

    registry = CalculationEngineRegistry()
    registry.register(InvalidResultEngine())
    invalid_runner = CalculationRunner(registry, runner._parameters)

    execution = invalid_runner.run(
        model,
        _request(model, method_code="TEST.INVALID_RESULT"),
    )

    assert execution.run.state == CalculationState.FAILED
    assert execution.run.error_message is not None
    assert "outside the input snapshot" in execution.run.error_message


def test_engine_registry_rejects_duplicate_method_revision() -> None:
    registry = CalculationEngineRegistry()
    registry.register(TotalLengthTestEngine())

    with pytest.raises(ValueError, match="already registered"):
        registry.register(TotalLengthTestEngine())



def test_identical_inputs_produce_identical_hashes(model_and_runner) -> None:
    model, _, runner = model_and_runner
    request = _request(model)

    first = runner.run(model, request)
    second = runner.run(model, request)

    assert first.run.input_hash == second.run.input_hash
    assert first.run.output_hash == second.run.output_hash


def test_run_and_save_preserves_project_edits_made_after_calculation_input_was_loaded(
    model_and_runner,
) -> None:
    model, project_repository, runner = model_and_runner
    latest_project = model.project.model_copy(
        update={"description": "Edited while calculation was being prepared."}
    )
    latest_model = model.model_copy(update={"project": latest_project})
    project_repository.save(latest_model)

    execution = runner.run_and_save(model, _request(model), project_repository)
    restored = project_repository.get(model.project.id)

    assert execution.run.state == CalculationState.COMPLETED
    assert restored.project.description == "Edited while calculation was being prepared."
    assert restored.calculation_runs[-1].id == execution.run.id
    assert restored.calculation_results[-1].calculation_run_id == execution.run.id



def test_run_and_save_rejects_calculation_when_an_input_object_changed(
    model_and_runner,
) -> None:
    model, project_repository, runner = model_and_runner
    first_pipe = next(item for item in model.objects if isinstance(item, LinearElement))
    changed_pipe = first_pipe.model_copy(
        update={"length": Quantity(value=Decimal(99), unit_code="meter")}
    )
    changed_objects = tuple(
        changed_pipe if item.id == first_pipe.id else item for item in model.objects
    )
    latest_model = model.model_copy(update={"objects": changed_objects})
    project_repository.save(latest_model)

    with pytest.raises(CalculationAppendError, match="changed after the run inputs"):
        runner.run_and_save(model, _request(model), project_repository)

    restored = project_repository.get(model.project.id)
    assert restored.objects == changed_objects
    assert restored.calculation_runs == latest_model.calculation_runs
