from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mechprox.data import models  # noqa: F401
from mechprox.data.db import Base
from mechprox.data.project_repository import (
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    ProjectRepository,
)
from mechprox.domain.model import EngineeringModel
from mechprox.domain.project import Project


@pytest.fixture
def repository(tmp_path: Path) -> ProjectRepository:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    return ProjectRepository(sessionmaker(bind=engine, expire_on_commit=False))


def test_project_snapshot_create_list_and_restore(repository: ProjectRepository) -> None:
    model = EngineeringModel(
        project=Project(project_code="TEST-001", name="Repository test project")
    )

    created = repository.create(model)
    listed = repository.list()
    restored = repository.get(model.project.id)

    assert created.id == model.project.id
    assert len(listed) == 1
    assert listed[0].project_code == "TEST-001"
    assert restored == model


def test_duplicate_project_code_is_rejected(repository: ProjectRepository) -> None:
    first = EngineeringModel(project=Project(project_code="DUP-001", name="First"))
    second = EngineeringModel(project=Project(project_code="DUP-001", name="Second"))
    repository.create(first)

    with pytest.raises(ProjectAlreadyExistsError):
        repository.create(second)


def test_missing_project_restore_is_explicit(repository: ProjectRepository) -> None:
    with pytest.raises(ProjectNotFoundError):
        repository.get(uuid4())


def test_project_snapshot_can_be_updated(repository: ProjectRepository) -> None:
    original = EngineeringModel(
        project=Project(project_code="SAVE-001", name="Original name")
    )
    repository.create(original)
    revised = original.model_copy(
        update={"project": original.project.model_copy(update={"name": "Revised name"})}
    )

    summary = repository.save(revised)

    assert summary.name == "Revised name"
    assert repository.get(original.project.id).project.name == "Revised name"
