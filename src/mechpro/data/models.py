from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mechpro.data.db import Base


class ParameterDefinition(Base):
    __tablename__ = "parameter_definitions"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String, unique=True)
    unit: Mapped[str] = mapped_column(String)
    standard_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    revision: Mapped[str | None] = mapped_column(String, nullable=True)

class ParameterValue(Base):
    __tablename__ = "parameter_values"
    id: Mapped[int] = mapped_column(primary_key=True)
    definition_id: Mapped[int] = mapped_column(ForeignKey("parameter_definitions.id"))
    value: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String)  # provenance
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)  # override scope
    definition: Mapped[ParameterDefinition] = relationship()
