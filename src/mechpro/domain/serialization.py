from mechpro.domain.model import EngineeringModel


def serialize_model(model: EngineeringModel, *, indent: int = 2) -> str:
    """Serialize a model snapshot to human-readable JSON."""
    return model.model_dump_json(indent=indent)


def deserialize_model(payload: str) -> EngineeringModel:
    """Restore and validate the typed model from JSON."""
    return EngineeringModel.model_validate_json(payload)
