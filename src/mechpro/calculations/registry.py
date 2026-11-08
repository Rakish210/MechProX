from mechpro.calculations.contracts import CalculationEngine


class CalculationEngineNotFoundError(LookupError):
    pass


class CalculationEngineRegistry:
    """Explicit registry of deterministic calculation engines and method revisions."""

    def __init__(self) -> None:
        self._engines: dict[tuple[str, str], CalculationEngine] = {}

    def register(self, engine: CalculationEngine) -> None:
        key = (engine.method_code, engine.method_revision)
        if not all(key) or not engine.engine_name or not engine.engine_version:
            raise ValueError("Calculation engine identity fields must be non-empty.")
        if key in self._engines:
            raise ValueError(
                f"Calculation engine method '{key[0]}' revision '{key[1]}' is already registered."
            )
        self._engines[key] = engine

    def get(self, method_code: str, method_revision: str) -> CalculationEngine:
        key = (method_code, method_revision)
        try:
            return self._engines[key]
        except KeyError as exc:
            raise CalculationEngineNotFoundError(
                f"No calculation engine is registered for '{method_code}' revision '{method_revision}'."
            ) from exc

    def all(self) -> tuple[CalculationEngine, ...]:
        return tuple(
            self._engines[key] for key in sorted(self._engines)
        )
