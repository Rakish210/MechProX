from mechprox.domain.base import Revision
from mechprox.domain.enums import CalculationPurpose
from mechprox.domain.validation_context import ValidationContext


def validate_calculation_records(ctx: ValidationContext) -> None:
    model = ctx.model

    for index, run in enumerate(model.calculation_runs):
        path = f"calculation_runs[{index}]"
        if run.project_id != model.project.id:
            ctx.add("wrong_project", "Calculation run belongs to a different project.", path)
        if run.purpose == CalculationPurpose.ENGINEERING:
            embedded_standard_ids = {item.id for item in run.standard_snapshots}
            if embedded_standard_ids != set(run.standard_reference_ids):
                ctx.add(
                    "calculation_standard_snapshot_mismatch",
                    "Engineering calculations must retain snapshots of all referenced standards.",
                    f"{path}.standard_snapshots",
                )
        for standard_id in run.standard_reference_ids:
            if standard_id not in ctx.standard_ids:
                ctx.add(
                    "missing_standard",
                    f"Calculation standard '{standard_id}' does not exist.",
                    f"{path}.standard_reference_ids",
                )

        for input_index, snapshot in enumerate(run.input_snapshots):
            input_path = f"{path}.input_snapshots[{input_index}]"
            if snapshot.engineering_object_id not in ctx.object_by_id:
                ctx.add(
                    "calculation_object_missing",
                    "Calculation input references an unknown engineering object.",
                    input_path,
                )
            if run.purpose == CalculationPurpose.ENGINEERING:
                if snapshot.object_snapshot is None:
                    ctx.add(
                        "calculation_object_snapshot_missing",
                        "Engineering calculations must retain a full object snapshot.",
                        input_path,
                    )
                else:
                    if (
                        snapshot.object_snapshot.id != snapshot.engineering_object_id
                        or snapshot.object_snapshot.revision_id != snapshot.object_revision_id
                    ):
                        ctx.add(
                            "calculation_object_snapshot_mismatch",
                            "The embedded object snapshot does not match its object/revision identifiers.",
                            input_path,
                        )
                    if snapshot.object_snapshot.properties != snapshot.property_snapshots:
                        ctx.add(
                            "calculation_property_snapshot_mismatch",
                            "Property snapshots do not match the embedded engineering object snapshot.",
                            input_path,
                        )
                for parameter_index, parameter in enumerate(snapshot.parameter_snapshots):
                    if parameter.revision_snapshot is None:
                        ctx.add(
                            "calculation_parameter_snapshot_missing",
                            "Engineering calculations must retain full parameter revision snapshots.",
                            f"{input_path}.parameter_snapshots[{parameter_index}]",
                        )
                    elif (
                        parameter.parameter_revision != str(parameter.revision_snapshot.id)
                        or parameter.value != parameter.revision_snapshot.value
                    ):
                        ctx.add(
                            "calculation_parameter_snapshot_mismatch",
                            "Parameter value/revision identifiers do not match the embedded revision snapshot.",
                            f"{input_path}.parameter_snapshots[{parameter_index}]",
                        )

            revision = ctx.revision_by_id.get(snapshot.object_revision_id)
            if revision is None or revision.object_id != snapshot.engineering_object_id:
                ctx.add(
                    "calculation_revision_missing",
                    "Calculation input must reference a revision of its source object.",
                    input_path,
                )
            ctx.validate_sources(snapshot.source_reference_ids, f"{input_path}.source_reference_ids")
            for property_index, prop in enumerate(snapshot.property_snapshots):
                property_path = f"{input_path}.property_snapshots[{property_index}]"
                ctx.validate_sources(prop.source_reference_ids, f"{property_path}.source_reference_ids")
                if prop.revision_id is not None:
                    ctx.require(prop.revision_id, Revision, f"{property_path}.revision_id", "Property revision")
                ctx.validate_property_value(prop.value, f"{property_path}.value")
            for parameter_index, parameter in enumerate(snapshot.parameter_snapshots):
                parameter_path = f"{input_path}.parameter_snapshots[{parameter_index}]"
                ctx.validate_sources(
                    parameter.source_reference_ids,
                    f"{parameter_path}.source_reference_ids",
                )
                ctx.validate_property_value(parameter.value, f"{parameter_path}.value")

    for index, result in enumerate(model.calculation_results):
        path = f"calculation_results[{index}]"
        run = ctx.run_by_id.get(result.calculation_run_id)
        if run is None:
            ctx.add(
                "calculation_run_missing",
                "Calculation result references an unknown run.",
                f"{path}.calculation_run_id",
            )
        else:
            captured_object_ids = {
                snapshot.engineering_object_id for snapshot in run.input_snapshots
            }
            captured_parameter_codes = {
                parameter.parameter_code
                for snapshot in run.input_snapshots
                for parameter in snapshot.parameter_snapshots
            }
            for object_id in result.source_object_ids:
                if object_id not in captured_object_ids:
                    ctx.add(
                        "result_source_not_captured",
                        "Result source object was not captured in the calculation inputs.",
                        f"{path}.source_object_ids",
                    )
            for parameter_code in result.source_parameter_codes:
                if parameter_code not in captured_parameter_codes:
                    ctx.add(
                        "result_parameter_not_captured",
                        f"Result parameter '{parameter_code}' was not captured in the calculation inputs.",
                        f"{path}.source_parameter_codes",
                    )

        ctx.validate_object_sources(result.source_object_ids, f"{path}.source_object_ids")
        ctx.validate_property_value(result.value, f"{path}.value")
        for standard_id in result.standard_reference_ids:
            if standard_id not in ctx.standard_ids:
                ctx.add(
                    "missing_standard",
                    f"Result standard '{standard_id}' does not exist.",
                    f"{path}.standard_reference_ids",
                )

    for index, approval in enumerate(model.approvals):
        if approval.revision_id not in ctx.revision_by_id:
            ctx.add(
                "approval_revision_missing",
                "Approval points to an unknown revision.",
                f"approvals[{index}].revision_id",
            )
