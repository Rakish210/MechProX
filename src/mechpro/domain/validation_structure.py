from mechpro.domain.base import Revision, SourceReference
from mechpro.domain.project import Project
from mechpro.domain.validation_context import ValidationContext


def validate_project_structure(ctx: ValidationContext) -> None:
    model = ctx.model

    for index, building in enumerate(model.buildings):
        path = f"buildings[{index}]"
        ctx.require(building.project_id, Project, f"{path}.project_id", "Building project")
        if building.project_id != model.project.id:
            ctx.add("wrong_project", "Building must belong to the model project.", path)

    building_ids = {item.id for item in model.buildings}
    for index, level in enumerate(model.levels):
        path = f"levels[{index}]"
        if level.building_id not in building_ids:
            ctx.add("missing_building", "Level references an unknown building.", f"{path}.building_id")
        if level.elevation is not None:
            ctx.validate_unit(level.elevation, f"{path}.elevation", "[length]")

    for index, space in enumerate(model.spaces):
        path = f"spaces[{index}]"
        if space.level_id not in ctx.level_ids:
            ctx.add("missing_level", "Space references an unknown level.", f"{path}.level_id")
        if space.area is not None:
            ctx.validate_unit(space.area, f"{path}.area", "[length] ** 2")
        if space.volume is not None:
            ctx.validate_unit(space.volume, f"{path}.volume", "[length] ** 3")

    for index, system in enumerate(model.systems):
        path = f"systems[{index}]"
        if system.project_id != model.project.id:
            ctx.add("wrong_project", "System must belong to the model project.", path)
        if system.discipline_code not in ctx.discipline_codes:
            ctx.add(
                "missing_discipline",
                f"Discipline '{system.discipline_code}' is not registered.",
                f"{path}.discipline_code",
            )

    for index, geometry in enumerate(model.geometry_references):
        if geometry.source_reference_id is not None:
            ctx.require(
                geometry.source_reference_id,
                SourceReference,
                f"geometry_references[{index}].source_reference_id",
                "Geometry source",
            )

    for index, standard in enumerate(model.standard_references):
        if standard.source_reference_id is not None:
            ctx.require(
                standard.source_reference_id,
                SourceReference,
                f"standard_references[{index}].source_reference_id",
                "Standard source",
            )

    for index, revision in enumerate(model.revisions):
        path = f"revisions[{index}]"
        if revision.parent_revision_id is not None:
            parent = ctx.require(
                revision.parent_revision_id,
                Revision,
                f"{path}.parent_revision_id",
                "Parent revision",
            )
            if parent is not None and parent.object_id != revision.object_id:
                ctx.add(
                    "revision_parent_mismatch",
                    "Parent revision belongs to a different object.",
                    f"{path}.parent_revision_id",
                )
        if revision.object_id not in ctx.revision_target_ids:
            ctx.add(
                "revision_object_missing",
                "Revision points to an unknown project/model record.",
                f"{path}.object_id",
            )
