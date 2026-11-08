import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from mechpro.calculations.contracts import (
    CalculationContext,
    CalculationExecution,
    CalculationOutput,
    CalculationRequest,
)
from mechpro.calculations.registry import CalculationEngineRegistry
from mechpro.data.parameter_registry_repository import ParameterRegistryRepository
from mechpro.data.project_repository import ProjectRepository
from mechpro.domain.base import StandardReference
from mechpro.domain.calculations import (
    CalculationInputSnapshot,
    CalculationResult,
    CalculationRun,
    ParameterSnapshot,
)
from mechpro.domain.engineering import EngineeringObjectRecord
from mechpro.domain.enums import CalculationState
from mechpro.domain.model import EngineeringModel
from mechpro.domain.parameters import ParameterRevision


class CalculationPreconditionError(ValueError):
    pass


class CalculationEngineContractError(RuntimeError):
    pass


class CalculationRunner:
    """Builds reproducible input snapshots and executes a registered engine."""

    def __init__(
        self,
        registry: CalculationEngineRegistry,
        parameter_repository: ParameterRegistryRepository,
    ) -> None:
        self._registry = registry
        self._parameters = parameter_repository

    def run(
        self,
        model: EngineeringModel,
        request: CalculationRequest,
    ) -> CalculationExecution:
        engine = self._registry.get(request.method_code, request.method_revision)
        context, input_snapshots, standard_ids = self._prepare_context(
            model, request, engine.required_parameter_codes
        )
        input_hash = self._digest(
            {
                "method_code": request.method_code,
                "method_revision": request.method_revision,
                "engine_name": engine.engine_name,
                "engine_version": engine.engine_version,
                "project_id": str(request.project_id),
                "effective_date": request.effective_date.isoformat(),
                "jurisdiction_code": request.jurisdiction_code,
                "purpose": request.purpose.value,
                "input_snapshots": [
                    snapshot.model_dump(mode="json") for snapshot in input_snapshots
                ],
                "standard_reference_ids": [str(item) for item in standard_ids],
            }
        )
        run = CalculationRun(
            id=uuid4(),
            project_id=model.project.id,
            method_code=engine.method_code,
            method_revision=engine.method_revision,
            engine_name=engine.engine_name,
            engine_version=engine.engine_version,
            purpose=request.purpose,
            state=CalculationState.RUNNING,
            started_at=datetime.now(UTC),
            input_snapshots=input_snapshots,
            standard_reference_ids=standard_ids,
            standard_snapshots=context.standard_references,
            input_hash=input_hash,
        )

        try:
            output = engine.calculate(context)
            self._validate_output(output, request, input_snapshots, standard_ids)
            results = tuple(
                CalculationResult(
                    calculation_run_id=run.id,
                    result_code=item.result_code,
                    label=item.label,
                    value=item.value,
                    source_object_ids=item.source_object_ids,
                    source_parameter_codes=item.source_parameter_codes,
                    standard_reference_ids=item.standard_reference_ids,
                )
                for item in output.results
            )
            output_hash = self._digest(
                {
                    "results": [
                        {
                            "result_code": item.result_code,
                            "label": item.label,
                            "value": item.value.model_dump(mode="json"),
                            "source_object_ids": [
                                str(value) for value in item.source_object_ids
                            ],
                            "source_parameter_codes": list(item.source_parameter_codes),
                            "standard_reference_ids": [
                                str(value) for value in item.standard_reference_ids
                            ],
                        }
                        for item in output.results
                    ],
                    "warnings": list(output.warnings),
                }
            )
            completed = run.model_copy(
                update={
                    "state": CalculationState.COMPLETED,
                    "completed_at": datetime.now(UTC),
                    "output_hash": output_hash,
                    "warnings": output.warnings,
                }
            )
            return CalculationExecution(
                run=completed,
                results=results,
                warnings=output.warnings,
            )
        except Exception as exc:  # noqa: BLE001 - engine failures must become persisted failed runs
            failed = run.model_copy(
                update={
                    "state": CalculationState.FAILED,
                    "completed_at": datetime.now(UTC),
                    "error_message": f"{type(exc).__name__}: {exc}",
                }
            )
            return CalculationExecution(
                run=failed,
                results=(),
                error=failed.error_message,
            )

    def run_and_save(
        self,
        model: EngineeringModel,
        request: CalculationRequest,
        project_repository: ProjectRepository,
    ) -> CalculationExecution:
        execution = self.run(model, request)
        updated_model = model.model_copy(
            update={
                "calculation_runs": (*model.calculation_runs, execution.run),
                "calculation_results": (
                    *model.calculation_results,
                    *execution.results,
                ),
            }
        )
        project_repository.save(updated_model)
        return execution

    def _prepare_context(
        self,
        model: EngineeringModel,
        request: CalculationRequest,
        required_parameter_codes: tuple[str, ...],
    ) -> tuple[
        CalculationContext,
        tuple[CalculationInputSnapshot, ...],
        tuple[UUID, ...],
    ]:
        if request.project_id != model.project.id:
            raise CalculationPreconditionError(
                "Calculation request project does not match the supplied model."
            )
        if not request.input_object_ids:
            raise CalculationPreconditionError(
                "At least one engineering object must be captured as a calculation input."
            )
        if len(set(request.input_object_ids)) != len(request.input_object_ids):
            raise CalculationPreconditionError("Calculation input object IDs must be unique.")
        if len(set(request.parameter_codes)) != len(request.parameter_codes):
            raise CalculationPreconditionError("Calculation parameter codes must be unique.")
        if len(set(request.standard_reference_ids)) != len(request.standard_reference_ids):
            raise CalculationPreconditionError("Calculation standard references must be unique.")

        missing_required = set(required_parameter_codes) - set(request.parameter_codes)
        if missing_required:
            raise CalculationPreconditionError(
                f"Required calculation parameters were not requested: {sorted(missing_required)}"
            )

        object_by_id = {item.id: item for item in model.objects}
        revision_by_id = {item.id: item for item in model.revisions}
        standard_by_id = {item.id: item for item in model.standard_references}
        selected_objects: list[EngineeringObjectRecord] = []

        for object_id in request.input_object_ids:
            item = object_by_id.get(object_id)
            if item is None:
                raise CalculationPreconditionError(
                    f"Calculation input object '{object_id}' does not exist."
                )
            if item.project_id != model.project.id:
                raise CalculationPreconditionError(
                    f"Calculation input object '{object_id}' belongs to another project."
                )
            object_revision_id = item.revision_id
            if object_revision_id is None:
                raise CalculationPreconditionError(
                    f"Calculation input object '{object_id}' has no controlled revision."
                )
            revision = revision_by_id.get(object_revision_id)
            if revision is None or revision.object_id != item.id:
                raise CalculationPreconditionError(
                    f"Calculation input object '{object_id}' has an invalid revision reference."
                )
            selected_objects.append(item)

        parameters: dict[str, ParameterRevision] = {}
        for code in request.parameter_codes:
            parameters[code] = self._parameters.resolve(
                code,
                jurisdiction_code=request.jurisdiction_code,
                project_id=request.project_id,
                effective_date=request.effective_date,
            )

        used_standard_ids = list(request.standard_reference_ids)
        for revision in parameters.values():
            for standard_id in revision.standard_reference_ids:
                if standard_id not in used_standard_ids:
                    used_standard_ids.append(standard_id)
        for standard_id in used_standard_ids:
            if standard_id not in standard_by_id:
                raise CalculationPreconditionError(
                    f"Calculation standard reference '{standard_id}' is not in the project model."
                )

        source_ids: set[UUID] = set()
        for item in selected_objects:
            source_ids.update(item.source_reference_ids)
            for prop in item.properties:
                source_ids.update(prop.source_reference_ids)
        for revision in parameters.values():
            source_ids.update(revision.source_reference_ids)
        known_source_ids = {item.id for item in model.source_references}
        missing_sources = source_ids - known_source_ids
        if missing_sources:
            raise CalculationPreconditionError(
                "Calculation input references source records not present in the project model: "
                + ", ".join(sorted(str(item) for item in missing_sources))
            )

        parameter_snapshots = tuple(
            ParameterSnapshot(
                parameter_code=code,
                value=revision.value,
                parameter_revision=str(revision.id),
                source_reference_ids=revision.source_reference_ids,
                revision_snapshot=revision,
            )
            for code, revision in parameters.items()
        )
        snapshots: list[CalculationInputSnapshot] = []
        for item in selected_objects:
            item_source_ids: set[UUID] = set(item.source_reference_ids)
            for prop in item.properties:
                item_source_ids.update(prop.source_reference_ids)
            item_source_ids.update(
                source_id
                for revision in parameters.values()
                for source_id in revision.source_reference_ids
            )
            payload = {
                "engineering_object_id": str(item.id),
                "object_revision_id": str(object_revision_id),
                "object_snapshot": item.model_dump(mode="json"),
                "properties": [
                    prop.model_dump(mode="json") for prop in item.properties
                ],
                "parameters": [
                    snapshot.model_dump(mode="json")
                    for snapshot in parameter_snapshots
                ],
                "source_reference_ids": [
                    str(value) for value in sorted(item_source_ids, key=str)
                ],
            }
            snapshots.append(
                CalculationInputSnapshot(
                    engineering_object_id=item.id,
                    object_revision_id=object_revision_id,
                    object_snapshot=item,
                    property_snapshots=item.properties,
                    parameter_snapshots=parameter_snapshots,
                    source_reference_ids=tuple(sorted(item_source_ids, key=str)),
                    snapshot_hash=self._digest(payload),
                )
            )

        standards: tuple[StandardReference, ...] = tuple(
            standard_by_id[item] for item in used_standard_ids
        )
        context = CalculationContext(
            model=model,
            request=request,
            input_objects=tuple(selected_objects),
            parameters=parameters,
            standard_references=standards,
        )
        return context, tuple(snapshots), tuple(used_standard_ids)

    @staticmethod
    def _validate_output(
        output: CalculationOutput,
        request: CalculationRequest,
        snapshots: tuple[CalculationInputSnapshot, ...],
        standard_ids: tuple[UUID, ...],
    ) -> None:
        if len({item.result_code for item in output.results}) != len(output.results):
            raise CalculationEngineContractError("Calculation result codes must be unique.")
        captured_objects = {item.engineering_object_id for item in snapshots}
        captured_parameters = {
            parameter.parameter_code
            for snapshot in snapshots
            for parameter in snapshot.parameter_snapshots
        }
        for result in output.results:
            if not set(result.source_object_ids).issubset(captured_objects):
                raise CalculationEngineContractError(
                    f"Result '{result.result_code}' references an object outside the input snapshot."
                )
            if not set(result.source_parameter_codes).issubset(captured_parameters):
                raise CalculationEngineContractError(
                    f"Result '{result.result_code}' references a parameter outside the input snapshot."
                )
            if not set(result.standard_reference_ids).issubset(set(standard_ids)):
                raise CalculationEngineContractError(
                    f"Result '{result.result_code}' references a standard outside the calculation context."
                )

    @staticmethod
    def _digest(payload: object) -> str:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
